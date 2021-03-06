---
title: 'iOS Backups in Racket: Contacts'
date: 2015-01-23
programming/languages:
- Racket
- Scheme
programming/topics:
- Backups
- Data Structures
- Databases
series:
- iOS Backups in Racket
---
After [yesterday's post]({{< ref "2015-01-22-ios-backup-groundwork.md" >}}) laying the groundwork for looking into [iOS Backups]({{< ref "2015-01-29-ios-backup-apps.md" >}}), today why don't we actually start digging into one of the more interesting files: your list of contacts.

<!--more-->

First things first, we have to find where the list of contacts is stored. That's the problem with the backup format--we have a giant list of files each of which is a SHA-1 hash. But of what?

Doing a little bit of digging, it looks like each of those hashes is based more or less on the filename of the source file. So if we happened to know that contacts are stored in the file `Library/AddressBook/AddressBook.sqlitedb`[^1], we should just be able to hash that:

```racket
> (call-with-input-string "Library/AddressBook/AddressBook.sqlitedb" sha1)
"adb8c77534444e97c31ff15924d50f3ed1fbd3b1"
```

Hmm. That file doesn't exist. But all of my sources are telling me that `AddressBook.sqlitedb` is in `HomeDomain`. What does that mean? Well it seems that iOS has some amount of sandboxing in it's filesystem, rather than a more traditional Unix style. Basically, the path is actually:

`Domain-Path`

Specifically:

```racket
; Hash attachments so that we can find the local path
(define (hash-filename path [domain "MediaDomain"])
  (for*/first ([prefix (in-list (list "/var/mobile/"
                                      "~/"
                                      ""))]
               #:when (and (> (string-length path) (string-length prefix))
                           (equal? (substring path 0 (string-length prefix)) prefix)))
    (define path-w/o-prefix (substring path (string-length prefix)))
    (call-with-input-string (~a domain "-" path-w/o-prefix) sha1)))
```

There's a bit of complication there. If a file uses a traditional Unix path, starting with with `/var/mobile/` or `~/` (the home directory), that is stripped off before adding the domain. If we try it again:

```racket
> (hash-filename "Library/AddressBook/AddressBook.sqlitedb" "HomeDomain")
"31bb7ba8914766d4ba40d6dfb6113c8b614be442"
```

Ah hah! That file actually exists (and matches the hash I've found online).

Let's poke around. First things first, let's load it up in `sqlite3`:

```sql
sqlite> .tables
ABAccount                        ABPersonFullTextSearch_segdir
ABGroup                          ABPersonFullTextSearch_segments
ABGroupChanges                   ABPersonFullTextSearch_stat
ABGroupMembers                   ABPersonLink
ABMultiValue                     ABPersonMultiValueDeletes
ABMultiValueEntry                ABPersonSearchKey
ABMultiValueEntryKey             ABPhoneLastFour
ABMultiValueLabel                ABRecent
ABPerson                         ABStore
ABPersonBasicChanges             FirstSortSectionCount
ABPersonChanges                  FirstSortSectionCountTotal
ABPersonFullTextSearch           LastSortSectionCount
ABPersonFullTextSearch_content   LastSortSectionCountTotal
ABPersonFullTextSearch_docsize   _SqliteDatabaseProperties
```

A lot of those are indicies or other things that we don't necessarily care about, but the first one that jumps out to me is `ABPerson`:

```sql
sqlite> .schema ABPerson
CREATE TABLE ABPerson (
  ROWID INTEGER PRIMARY KEY AUTOINCREMENT,
  First TEXT,
  Last TEXT,
  Middle TEXT,
  FirstPhonetic TEXT,
  MiddlePhonetic TEXT,
  LastPhonetic TEXT,
  Organization TEXT,
  Department TEXT,
  Note TEXT,
  Kind INTEGER,
  Birthday TEXT,
  JobTitle TEXT,
  Nickname TEXT,
  Prefix TEXT,
  Suffix TEXT,
  FirstSort TEXT,
  LastSort TEXT,
  CreationDate INTEGER,
  ModificationDate INTEGER,
  CompositeNameFallback TEXT,
  ExternalIdentifier TEXT,
  ExternalModificationTag TEXT,
  ExternalUUID TEXT,
  StoreID INTEGER,
  DisplayName TEXT,
  ExternalRepresentation BLOB,
  FirstSortSection TEXT,
  LastSortSection TEXT,
  FirstSortLanguageIndex INTEGER DEFAULT 2147483647,
  LastSortLanguageIndex INTEGER DEFAULT 2147483647,
  PersonLink INTEGER DEFAULT -1,
  ImageURI TEXT,
  IsPreferredName INTEGER DEFAULT 1,
  guid TEXT DEFAULT (ab_generate_guid()),
  PhonemeData TEXT,
  AlternateBirthday TEXT,
  MapsData TEXT,
  UNIQUE(guid)
);
...
```

There is rather a pile of other statements after that, but that's the table that we're interested in. Specifically, that at least has the names and organizations (which at the moment is what I'm really interested in). What's suspiciously absent though, is the phone numbers. Hmm...

After a little bit of digging, I came across this table:

```sql
sqlite> .schema ABMultiValue
CREATE TABLE ABMultiValue (
  UID INTEGER PRIMARY KEY,
  record_id INTEGER,
  property INTEGER,
  identifier INTEGER,
  label INTEGER,
  value TEXT,
  guid TEXT DEFAULT (ab_generate_guid()),
  UNIQUE(guid)
);
```

Specifically, `record_id` matches `ABPerson.ROWID` and `value` contains phone numbers, email address, etc. (This is the real reason that I wrote the `normalize-contact` function).

Okay. That should be enough for the moment. Let's switch gears and lay out a similar framework to `backup`.

```racket
(define CONTACTS-DB
  (hash-filename "Library/AddressBook/AddressBook.sqlitedb" "HomeDomain"))

; Name is a human readable name for a contact
; Identifiers is a list of phone numbers / emails / etc
(struct contact (name identifiers) #:prefab)

; Store a separate list of contacts for each backup (potentially)
(define contacts-by-backup (make-hash))
(hash-set! contacts-by-backup #f '())
```

Cool. Now we want to load the specific list of contacts, caching them the same way we did with the backups themselves:

```racket
; Load all contacts stored in a specific backup
(define (list-contacts)
  (hash-ref!
   contacts-by-backup
   (current-backup)
   (λ ()
     (define contacts-db
       (sqlite3-connect #:database (build-path (backup-path (current-backup))
                                               CONTACTS-DB)))

     (for/list ([(user-id first-name middle-name last-name organization)
                 (in-query contacts-db "SELECT ROWID, First, Middle, Last, Organization FROM ABPerson")])

       (define (fix str) (if (sql-null? str) "" str))

       (define name
         (let* ([name (~a (fix first-name) " "
                          (fix middle-name) " "
                          (fix last-name) " "
                          "(" (fix organization) ")")]
                [name (regexp-replace* #px"\\(\\)" name "")]
                [name (regexp-replace* #px"\\s+" name " ")]
                [name (string-trim name)]
                [name (regexp-replace* #px"^\\((.*)\\)$" name "\\1")])
           name))

       (define identifiers
         (for*/list ([raw-value (in-list (query-list contacts-db "SELECT value FROM ABMultiValue WHERE record_id = $1" user-id))]
                     [value (in-value (normalize-contact raw-value))]
                     #:when value)
           value))

       (contact name identifiers)))))
```

Basically, we want to make a nested set of queries, first one for each user and then another for all contact information for that user. It's Not the perfect way of doing itl as theoretically we could have done a sql join, but it works well enough.

As far as the name formatting, that's just the way I needed it to work. When I get around to it, I'll probably write a `name-display-format` parameter akin to {{< doc racket "date-display-format" >}} from {{< doc racket "racket/date" >}}. Not today though!

So let's see how it works:

```racket
> (with-backup "86b18eea28a991f4dd569d1f59737a842e24aa36"
    (list-contacts))
'(#s(contact "Charles I. Clarke" ("555.555.1234" "charlie.c@example.com"))
  #s(contact "Jenny Reichert (Catsitter)" ("555.867.5309"))
  #s(contact "Mary Orndorff" ("555.555.0000"))
  #s(contact "Pizza Palace" ("555.555.1123"))
  #s(contact "Willie S. Culpepper" ("555.555.1491"))
  ...)
```

Sweet.

And as a bonus, let's include a basic search function:

```racket
; Load a user by name or value
(define (find-contact key)
  (for/first ([contact (in-list (list-contacts))]
              #:when (or (equal? key (contact-name contact))
                         (member key (contact-identifiers contact))))
    contact))
```

Again, it's not a fuzzy match (you have to have the name exact), but that's something I'll probably clean up later.

```racket
> (with-backup "86b18eea28a991f4dd569d1f59737a842e24aa36"
    (find-contact "Charles I. Clarke"))
#s(contact
   "Charles I. Clarke"
   ("555.555.1234" "charlie.c@example.com")
```

And there you have it. Contacts. We're really starting to get somewhere here. Next week (probably Monday or Tuesday), I'll write up messages (both SMS and iMessage). That one will really be fun.

As always entire code for today's post is available on GitHub: <a href="https://github.com/jpverkamp/ios-backup">ios-backup</a>

Here is a list of all of the posts in this series:

{{< taxonomy-list "series" "iOS Backups in Racket" >}}

[^1]: <a href="https://theiphonewiki.com/wiki/ITunes_Backup#Files">theiphonewiki.com</a>
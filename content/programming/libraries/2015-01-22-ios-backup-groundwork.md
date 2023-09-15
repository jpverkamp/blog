---
title: 'iOS Backups in Racket: Groundwork'
date: 2015-01-22
programming/languages:
- Racket
- Scheme
programming/topics:
- Backups
- Data Structures
series:
- iOS Backups in Racket
---
For the last little while, I've been spending my spare programming time working on a slightly larger project than I normally do: a [Racket]({{< ref "2014-06-11-call-stack-bracket-matcher.md" >}}) library for reading iOS backups.

Basically, I want to take the mess that is an iOS backup (not particularly designed to be easy to read by other programs) and extract some information from it, backing it up in a more easily readable format.

Specifically, I would like to be able to backup:


* Contact information: Even thought they're mostly from Facebook, it will be useful for the other parts
* Messages: These are taking up a large portion of my phone's hard drive, mostly due to attachments. Back them up just in case[^1][^2]
* Photos: I'm already backing these up, but it would be nice to have it in the same process
* Application data: 
* List of applications over time
* [Moves](https://www.moves-app.com/): GPS location
* [Downcast](http://www.downcastapp.com/): List of current podcasts
* [Sleep Cycle](http://www.sleepcycle.com/): Sleep data
* [Boardgame Scorer](http://www.boardgamescorer.com/): High scores for board games


<!--more-->

The first thing to look at is the basic structure of the iOS backup directory:

```text
~/Library/Application Support/MobileSync/Backup/
    86b1...aa36/
        0003...1b9a
        0009...521c
        000b...46ab
        ...
        fff6...5152
        fff8...9f8a
        fffa...ca34
        Info.plist
        Manifest.mbdb
        Manifest.plist
        Status.plist
```

Okay, that's helpful[^3]. 6788 files, all but four of which named via [[wiki:SHA-1]]() hashes. I know that there are pictures, applications, and various databases here, so there has to be a map somewhere.

But first, those last four files:


* `Info.plist` - Contains information about the backup, including the phone's name, various IDs, the phone's number, and versioning information
* `Manifest.mbdb` - Binary file containing a listing of every file in the backup
* `Manifest.plist` - Legacy file, useful information is mostly a list of installed applications
* `Status.plist` - Mostly a subset of the information in `Info.plist`


Of those, we'll start with the first one. We want to be able to load that information into a basic structure to represent a backup:

```racket
; Represents an iPhone backup on disk
(struct backup (name hash date phone-number path) #:prefab)
```

Cool. First thing first, let's find the backups on disk. We want to be able to support either Windows or OSX (I use both), so try both locations:

```racket
; Load all backups on disk into a list
(define list-backups
  (let* (; OS agnostic (I hope) way of finding the backup root
         [backup-root
          (for*/first ([path-parts (in-list '(("AppData" "Roaming" "Apple Computer"
                                               "MobileSync" "Backup")
                                              ("Library" "Application Support"
                                                "MobileSync" "Backup")))]
                       [path (in-value (apply build-path
                                              (cons (find-system-path 'home-dir)
                                                    path-parts)))]
                       #:when (directory-exists? path))
            path)]

         ; List all backups in that directory, along with some metadata
         [backups
          (for/list ([dir (in-list (directory-list backup-root))])
            (define info-file
              (call-with-input-file (build-path backup-root dir "Info.plist")
                read-plist/jsexpr))

            (backup (dict-ref info-file '|Device Name|)
                    (path->string dir)
                    (dict-ref info-file '|Last Backup Date|)
                    (normalize-contact (dict-ref info-file '|Phone Number|))
                    (build-path backup-root dir)))])

    (λ () backups)))
```

The function is a little strange looking, mostly because of caching. Rather than scanning and loading the backup every time we want a list, scan it once on load, then return that whenever the function is called.

One thing missing though, we have to define the function `read-plist/jsexpr` yet. Luckily, we have the {{< doc racket "xml/plist" >}} library to handle the first part of this[^4], but personally I'd rather a more straight forward format (a {{< doc racket "jsexpr" >}} is basically a mix of hashes, lists, and atoms):

```racket
; Convert a plist into a JSON expression
(define (plist->jsexpr data)
  (match data
    [(? string?) data]
    [`(true) #t]
    [`(false) #f]
    [`(integer ,v) v]
    [`(real ,v) v]
    [`(data ,v) v] ; Should we special case these?
    [`(date ,v) v] ; Ditto
    [`(array . ,v*)
     (map plist->jsexpr v*)]
    [`(dict . ,kv*)
     (for/hash ([kv (in-list kv*)])
       (values (string->symbol (second kv)) (plist->jsexpr (third kv))))]))

; Read a plist file as a JSON expression from a file
(define (read-plist/jsexpr [in (current-input-port)])
  (plist->jsexpr (read-plist in)))
```

I still haven't decided if special casing `data` and `date` elements is worthwhile.

The other interesting function is another utility function `normalize-contact`:

```racket
; Process a phone number or email address into a common format
(define (normalize-contact value)
  (define re #px"^\\+?1? ?[\\(\\.]?(\\d\\d\\d)[\\)\\.-]? ?(\\d\\d\\d)[ \\.-]?(\\d\\d\\d\\d)$")
  (cond
    [(sql-null? value)
     #f]
    ; Standard phone numbers
    ; TODO: Figure out international numbers
    [(regexp-match re value)
     => (λ (match) (string-join (rest match) "."))]
    ; Email addresses
    [(regexp-match #px"^[^@]+@[^@]+$" value)
     value]
    ; Short phone numbers
    [(regexp-match #px"^\\d{,6}$" value)
     value]
    ; No idea...
    [else #f]))
```

Phone numbers in an iPhone backup are stored all sorts of odd ways. In particular, once you start looking at the contacts, you can get three or four different formats just for normal area code + 7 phone numbers (I haven't yet decided how to support international numbers). So this can be used to at least put them all in the same format.

But with that, we now have the ability to list all backups on the local system:

```racket
> (list-backups)
'(#s(backup
     "JP’s iPhone"
     "63b5...a651"
     "2014-04-17T21:53:16Z"
     "{redacted}"
     #<path:/Users/jp/Library/Application Support/MobileSync/Backup/63b5....a651>))
```

It's an older backup, but that's fine.

Next, what if we have more than one backup on the system? It would be nice to have a function that could take that list of backups and load just one (that other parts of the library can access) based on name/hash/phone number:

```racket
; Store the most recently used backup for other modules
(define current-backup (make-parameter #f))

; Load a specific backup, try to guess what the identifier is
(define (read-backup identifier)
  (for/first ([backup (in-list (list-backups))]
              #:when (or (equal? identifier (backup-date backup))
                         (equal? identifier (backup-name backup))
                         (equal? identifier (backup-hash backup))
                         (equal? identifier (backup-phone-number backup))))
    backup))
```

Fair enough. At the moment, you have to have an exact match, but that's fine. If we want to later, we could replace the calls to {{< doc racket "equal?" >}} with {{< doc racket "regexp-match" >}}.

So now I can find my own backup:

```racket
> (read-backup "86b1...aa36")
'#s(backup
    "JP’s iPhone"
    "63b5...a651"
    "2014-04-17T21:53:16Z"
    "{redacted}"
    #<path:/Users/jp/Library/Application Support/MobileSync/Backup/63b5....a651>)
```

One more utility macro:

```racket
; Parameterize code with a current backup
(define-syntax-rule (with-backup identifier body ...)
  (parameterize ([current-backup (read-backup identifier)])
    body ...))
```

This will be nice, since it can let us do things like this:

```racket
> (define contacts
    (with-backup "86b1...aa36"
      (list-contacts)))
```

Nice and clean.

I think that's about enough for today. The entire code for today's post (along with the entire library thus far, which is significantly further along[^5]), is available on GitHub: <a href="https://github.com/jpverkamp/ios-backup">ios-backup</a>

Here is a list of all of the posts in this series:

{{< taxonomy-list "series" "iOS Backups in Racket" >}}

[^1]: Yeah, I know I'm something of a digital packrat. ¯\\_(ツ)_/¯ Disk space is cheap.
[^2]: Except on iPhones. Seriously, that's the only difference within a model, yes?
[^3]: For some definitions of helpful...
[^4]: Sort of. Turns out that library doesn't handle binary plists. We'll work around that when we handle applications.
[^5]: Although still somewhat lacking in documentation
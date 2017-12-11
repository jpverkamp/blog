---
title: 'iOS Backups in Racket: Messages'
date: 2015-01-27
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
So far we've [laid the groundwork]({{< ref "2015-01-22-ios-backup-groundwork.md" >}}), loading local iOS backups and parsed out [contacts]({{< ref "2015-01-23-ios-backup-contacts.md" >}}). Today let's take another step down the rabbit hole and figure out how messages are stored.

<!--more-->

Okay, first things first, we need to find the database(s) that messages are stored in. Using the <a href="https://theiphonewiki.com/wiki/ITunes_Backup#Files">same source</a> as last time, we have:

```racket
> (hash-filename "Library/SMS/sms.db" "HomeDomain")
"3d0d7e5fb2ce288813306e4d4636395e047a3d28"
```

Interesting. What's in there?

```sql
sqlite> .tables
_SqliteDatabaseProperties  chat_message_join
attachment                 handle
chat                       message
chat_handle_join           message_attachment_join
```

Dang. That's rather less than there was when dealing with contacts. From a first guess, I would say that `message` contains the text itself, `chat` is a group of messages with the same people, and `*_join` are tables that related those. `handle` could perhaps be a way of relating who is in a chat to the information in contacts from last week. Let's see how I did:

```sql
CREATE TABLE message (ROWID INTEGER PRIMARY KEY AUTOINCREMENT,
    guid TEXT UNIQUE NOT NULL,
    text TEXT,
    replace INTEGER DEFAULT 0,
    service_center TEXT,
    handle_id INTEGER DEFAULT 0,
    subject TEXT,
    country TEXT,
    attributedBody BLOB,
    version INTEGER DEFAULT 0,
    type INTEGER DEFAULT 0,
    service TEXT,
    account TEXT,
    account_guid TEXT,
    error INTEGER DEFAULT 0,
    date INTEGER,
    date_read INTEGER,
    date_delivered INTEGER,
    is_delivered INTEGER DEFAULT 0,
    is_finished INTEGER DEFAULT 0,
    is_emote INTEGER DEFAULT 0,
    is_from_me INTEGER DEFAULT 0,
    is_empty INTEGER DEFAULT 0,
    is_delayed INTEGER DEFAULT 0,
    is_auto_reply INTEGER DEFAULT 0,
    is_prepared INTEGER DEFAULT 0,
    is_read INTEGER DEFAULT 0,
    is_system_message INTEGER DEFAULT 0,
    is_sent INTEGER DEFAULT 0,
    has_dd_results INTEGER DEFAULT 0,
    is_service_message INTEGER DEFAULT 0,
    is_forward INTEGER DEFAULT 0,
    was_downgraded INTEGER DEFAULT 0,
    is_archive INTEGER DEFAULT 0,
    cache_has_attachments INTEGER DEFAULT 0,
    cache_roomnames TEXT,
    was_data_detected INTEGER DEFAULT 0,
    was_deduplicated INTEGER DEFAULT 0,
    is_audio_message INTEGER DEFAULT 0,
    is_played INTEGER DEFAULT 0,
    date_played INTEGER,
    item_type INTEGER DEFAULT 0,
    other_handle INTEGER DEFAULT -1,
    group_title TEXT,
    group_action_type INTEGER DEFAULT 0,
    share_status INTEGER,
    share_direction INTEGER,
    is_expirable INTEGER DEFAULT 0,
    expire_state INTEGER DEFAULT 0,
    message_action_type INTEGER DEFAULT 0,
    message_source INTEGER DEFAULT 0
 );
```

Oof. Okay, that's more like what I was expecting. In particular though, it looks like we don't care about most of those fields. In particular, I think the interesting fields will be `guid`, `text`, `handle_id` (it looks like we will need the `handle` table), `date`, and `is_from_me`.

Next, `chat`:

```sql
sqlite> .schema chat
CREATE TABLE chat (ROWID INTEGER PRIMARY KEY AUTOINCREMENT,
    guid TEXT UNIQUE NOT NULL,
    style INTEGER,
    state INTEGER,
    account_id TEXT,
    properties BLOB,
    chat_identifier TEXT,
    service_name TEXT,
    room_name TEXT,
    account_login TEXT,
    is_archived INTEGER DEFAULT 0,
    last_addressed_handle TEXT,
    display_name TEXT,
    group_id TEXT
);
```

Hmm. It turns out that we don't actually need anything there. All that we need to know about chats is which ID we need, which because it's a join table, that will be in `chat_message_join`:

```sql
sqlite> .schema chat_message_join
CREATE TABLE chat_message_join (
    chat_id INTEGER REFERENCES chat (ROWID) ON DELETE CASCADE,
    message_id INTEGER REFERENCES message (ROWID) ON DELETE CASCADE,
    PRIMARY KEY (chat_id, message_id)
);
```

So if we have a chat ID, we can get all of that information:

```sql
SELECT
  message.ROWID as message_id,
  message.date,
  message.service,
  message.is_from_me,
  (CASE WHEN message.subject IS NULL THEN '' ELSE message.subject END),
  (CASE WHEN message.text IS NULL THEN '' ELSE message.text END)
FROM
  chat_message_join,
  message
WHERE
  chat_id = ?
  AND message_id = message.ROWID
ORDER BY date ASC
```

The conversion from `NULL` to an empty string is mostly for later. I know that I'll want to serialize these, most likely to JSON and I don't particularly care about the difference between a `NULL` entry and an empty string.

That's a good start. We still need to know who they're from though.

```sql
sqlite> .schema handle
CREATE TABLE handle (
    ROWID INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
    id TEXT NOT NULL,
    country TEXT,
    service TEXT NOT NULL,
    uncanonicalized_id TEXT,
    UNIQUE (id,
    service)
);
```

Looking at some of the values, it seems that `id` is either an email or a phone number, while service is either SMS or iMessage (at least in my case). Country might be interesting later, but we'll ignore it for the moment.

So let's expand the query to include that information:

```sql
SELECT
  message.ROWID as message_id,
  message.date,
  message.service,
  message.is_from_me,
  handle.id as them,
  (CASE WHEN message.subject IS NULL THEN '' ELSE message.subject END),
  (CASE WHEN message.text IS NULL THEN '' ELSE message.text END)
FROM
  chat_message_join,
  message,
  handle
WHERE
  chat_id = ?
  AND message_id = message.ROWID
  AND handle_id = handle.ROWID
ORDER BY date ASC
```

Cool. One last thing. Remember that `attachment` table? Let's go ahead and add that in, just loading the attachments as a single string:

```sql
SELECT
  message.ROWID as message_id,
  message.date,
  message.service,
  message.is_from_me,
  handle.id as them,
  (CASE WHEN message.subject IS NULL THEN '' ELSE message.subject END),
  (CASE WHEN message.text IS NULL THEN '' ELSE message.text END),
  (SELECT group_concat(attachment.filename)
     FROM message_attachment_join, attachment
     WHERE message_attachment_join.message_id = message.ROWID
       AND message_attachment_join.attachment_id = attachment.ROWID)
FROM
  chat_message_join,
  message,
  handle
WHERE
  chat_id = ?
  AND message_id = message.ROWID
  AND handle_id = handle.ROWID
ORDER BY date ASC
```

Okay. They say that {{< figure link="https://www.youtube.com/watch?v=pele5vptVgc" src="/embeds/2015/knowing is half the battle" >}}, so having all of the structure and that SQL query should translate pretty directly to code:

```racket
(struct chat (contacts messages) #:prefab)
(struct message (date service sender subject text attachments) #:prefab)
(struct attachment (name path) #:prefab)

; Load all chats from a backup directory
(define (list-chats)
  (hash-ref!
   chats-by-backup
   (current-backup)
   (λ ()
     (parameterize ([date-display-format 'iso-8601])
       ; Connect to the correct DB
       (define sms-db
         (sqlite3-connect
           #:database (build-path (backup-path (current-backup))
                                  MESSAGES-DB)))

       ; Loop over the individual chat ids
       (for/list ([(chat-id) (in-query sms-db "SELECT ROWID FROM chat")])
         ; Determine which contacts were involved in the conversation by contact
         ; Use models/contacts.rkt to figure out who belongs to contact information
         (define user-query "SELECT id FROM chat_handle_join, handle
                             WHERE chat_id = $1 AND handle_id = ROWID
                             ORDER BY handle_id ASC")
         (define contacts
           (for/list ([(contact) (in-query sms-db user-query chat-id)])
             (find-contact (normalize-contact contact))))

         ; Load the individual messages
         (define msg-query "
SELECT
  message.ROWID as message_id,
  message.date,
  message.service,
  message.is_from_me,
  handle.id as them,
  (CASE WHEN message.subject IS NULL THEN '' ELSE message.subject END),
  (CASE WHEN message.text IS NULL THEN '' ELSE message.text END),
  (SELECT group_concat(attachment.filename)
     FROM message_attachment_join, attachment
     WHERE message_attachment_join.message_id = message.ROWID
       AND message_attachment_join.attachment_id = attachment.ROWID)
FROM
  chat_message_join,
  message,
  handle
WHERE
  chat_id = ?
  AND message_id = message.ROWID
  AND handle_id = handle.ROWID
ORDER BY date ASC")
         (define messages
           (for/list ([(message-id
                        raw-date
                        service
                        from-me?
                        other-party
                        subject
                        text
                        raw-attachments)
                       (in-query sms-db msg-query chat-id)])
             ; Correct dates from Apple time to unix time
             ; TODO: Account for timezones?
             (define date (seconds->date (+ raw-date 978336000 (- (* 16 60 60))) #f))

             (define sender
               (if (= 1 from-me?)
                   (backup-phone-number (current-backup))
                   (normalize-contact other-party)))

             ; Load attachments,
             (define attachments
               (if (sql-null? raw-attachments)
                   '()
                   (for/list ([path (in-list (string-split raw-attachments ","))])
                     (attachment
                      (path->string (last (explode-path path)))
                      (build-path (backup-path (current-backup))
                                  (hash-filename path))))))

             (message date service sender subject text attachments)))

         ; Create the chat object
         (chat contacts messages))))))
```

Theoretically, that should be a fairly direct translation. One interesting bit is the format of `date`. It's actually a timestamp, but not a normal {{< wikipedia "Unix timestamp" >}}. So I have a bit of a {{< wikipedia "magic number" >}}, but it works correctly for my backups, so we'll just leave it for the moment. Other than that, we use the `hash-filename` function from last time to get a local path for any `attachment` and we've got everything pretty much written.

And that's really all we need. One thing that would be nice to be able to do though is, given a contact, filter for only the messages with that contact (either directly or in group chats as well):

```racket
; Get all chats involving a specific chat
(define (find-chats-by-contact contact #:direct? [direct? #f])
  ; Allow the user to specify the contact by name / phone number / email / etc
  (when (not (contact? contact))
    (set! contact (find-contact contact)))

  ; Filter the list of chats
  (for/list ([chat (in-list (list-chats))]
             #:when (if direct?
                        (equal? (list contact) (chat-contacts chat))
                        (member contact (chat-contacts chat))))
    chat))
```

If you have an iOS device, check it out. It makes certain things really easy. For example, if I want to have a log of every word that I've ever said in a conversation with Jenny:

```racket
> (with-backup "86b18...aa36"
    (for*/list ([chat (in-list (find-chats-by-contact "Jenny" #:direct? #t))]
                [message (in-list (chat-messages chat))])
      (message-text message)))
'("Jenny, Jenny, who can I turn to?"
  "You give me somethin' I can hold on to"
  ...)
```

That's exactly the sort of that prompted this entire thought: the ability to take the fairly opaque structure of iOS backups and dump them into an easily readable / easily diffable format for my own purposes. Sweet.


If you'd like to see the entire project, you can do so on GitHub: <a href="https://github.com/jpverkamp/ios-backup">ios-backup</a>. Alternatively, it's set up as a package, so you should be able to install it with `raco pkg install`. If you do, just import one or more of these:

```racket
(require ios-backup
         ios-backup/contacts
         ios-backup/messages)
```

Here is a list of all of the posts in this series:

{{< taxonomy-list "series" "iOS Backups in Racket" >}}

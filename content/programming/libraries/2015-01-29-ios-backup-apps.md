---
title: 'iOS Backups in Racket: Apps'
date: 2015-01-29
programming/languages:
- Racket
- Scheme
programming/topics:
- Backups
- Data Structures
- File Formats
series:
- iOS Backups in Racket
---
So far we've read [backup files]({{< ref "2015-01-22-ios-backup-groundwork.md" >}}), parsed [contacts]({{< ref "2015-01-23-ios-backup-contacts.md" >}}), and parsed [messages]({{< ref "2015-01-27-ios-backup-messages.md" >}}). Today we're going to dig a little deeper and start parsing apps specifically.

<!--more-->

First things first, let's get a list of applications. That's actually in two different files: `Manifest.plist` and `Manifest.mbdb`. In versions of iTunes prior to 9.2, `Manifest.plist` had a nice listing of files, but now it only contains the list of applications. Still, that's a good enough place to start.

Remember back in the [first post]({{< ref "2015-01-22-ios-backup-groundwork.md" >}})? We learned how how to read plist files. In this one in particular, we have a list of installed applications, using their internal names:

```racket
(struct app (name plist files) #:prefab #:mutable)
(struct file (name path) #:prefab)

; List all installed applications
(define (list-apps)
  (hash-ref!
   apps-by-backup
   (current-backup)
   (λ ()
     (for/list ([name (in-list
                       (hash-ref
                        (call-with-input-file
                          (build-path (backup-path (current-backup))
                                                   "Info.plist")
                          read-plist/jsexpr)
                        '|Installed Applications|))])
       (app name #f #f)))))
```

For the moment, we'll leave out the plist and files. Eventually, plist is going to store a list of properties stored with the application (all apps have it, even if some don't store anything interesting). Files will store any files stored in the local filesystem for app in specific.

So how does it work?

```racket
> (with-backup "86b1...aa36"
    (map app-name (list-apps)))
'("com.google.Maps"
  "com.apple.mobilesms.notification"
  "com.roku.ios.roku"
  ...
  "com.apple.iBooks"
  "com.apple.MobileSMS"
  "com.apple.CoreAuthUI")
```

Neat. That's pretty much exactly what I was hoping to see.

Next, let's load up the plists. On doing some digging around, it looks like every app will have a file with a path something like `AppDomain-Library/Preferences/{app-name}.plist`, so let's try to load that:

```racket
; Load an app's plist file
(define (load-plist! app)
  (set-app-plist!
   app
   (let ([plist-path
          (build-path
           (backup-path (current-backup))
           (hash-filename
            (~a "Library/Preferences/" (app-name app) ".plist")
            (~a "AppDomain-" (app-name app))))])

     ; Try to load in text mode first, if that fails fall back to binary
     (with-handlers ([exn? (λ (exn)
                             (call-with-input-file plist-path
                               read-plist/jsexpr/binary))])
       (call-with-input-file plist-path read-plist/jsexpr)))))
```

Here we run into our first wrinkle. It turns out that while the {{< doc racket "xml/plist" >}} file works just fine on the text format plist files, it doesn't deal well with binary ones. And unfortunately most (if not all) apps use the binary format. So we need something that will be able to convert and load those (warning, this is ugly):

```racket
; Read a plist file as a JSON expression from a binary plist file
(define (read-plist/jsexpr/binary [in (current-input-port)])
  ; Copy the file to a temporary path
  (define temp-filename (~a (gensym) ".plist"))
  (call-with-output-file temp-filename
    (λ (out) (copy-port in out)))

  ; Run Apple's plutil to convert it
  ; Redirect err to suppress from missing programs
  (parameterize ([current-error-port (open-output-nowhere)])
    (for* ([path
            (in-list
              '("plutil"
                "plutil.exe"
                "\"C:\\Program Files (x86)\\Common Files\\Apple\\Apple Application Support\\plutil.exe\""
                ""\"C:\\Program Files\\Common Files\\Apple\\Apple Application Support\\plutil.exe\""))]
           [return (in-value (system (~a path " -convert xml1 " temp-filename)))]
           #:break return)
      #t))

  ; Patch over xml/plist's handling of empty string element
  (define plist-fixed-content
    (regexp-replace* #px"<string></string>"
                     (file->string temp-filename)
                     "<string> </string>"))
  (delete-file temp-filename)

  ; Read the plist into memory and remove the temporary file
  (call-with-input-string plist-fixed-content read-plist/jsexpr))
```

Basically, if you have iTunes installed, it comes with a program (on Windows, it's built in on OSX) called `plutil`. That can be used to convert between binary, xml, and json formats of plist files. Unfortunately though, the json format cannont handle a lot of plists, so we have to convert to xml and then use our previous `plist->jsexpr` function to convert it.

Other hacks: we have to copy it to a temporary file. It's probably possible to open `plutil` and pass the file on stdin and read from stdout instead, but this works so we'll leave it as is for the moment.

Finally, another caveat of the {{< doc racket "xml/plist" >}} library: it breaks on empty string elements. So there's a fix above to take any empty string elements and insert a single space into them. Hacky, but so it goes. When all this is said and done though, we can use this to read in the plist data for an application:

```racket
> (with-backup "86b18eea28a991f4dd569d1f59737a842e24aa36"
    (let ([app (list-ref (list-apps) 12)])
      (load-plist! app)
      app))

'#s((app #(0 1 2))
    "com.google.Maps"
    #hash((WebKitCacheModelPreferenceKey . 1)
          (WebKitDiskImageCacheSavedCacheDirectory . " ")
          (WebKitMediaPlaybackAllowsInline . #t)
          (WebKitOfflineWebApplicationCacheEnabled . #t)
          (WebKitShrinksStandaloneImagesToFit . #t)
          ...
          (kGIPMicPermissionControllerPermissionRequested . #t)
          (kGMSMapsUserClientLegalCountry . "US")
          (kGMSUserEvent3LoggerSequenceIDKey . 8860))
    #f)
```

Whee! For any particular app, I'm not entirely sure what I'm looking for, but there's a whole heck of a lot of information there.

But one thing that I was hoping to find is still missing: a list of files for a given application. I was hoping each application would know that, but apparently not. Then again, why would they? A given application probably knows exactly what files it's looking for, it doesn't have to list them.

Fine. I guess I have to read that `Manifest.mbdb` file.

```bash
$ xxd "Manifest.mbdb"

0000000: 6d62 6462 0500 001d 4170 7044 6f6d 6169  mbdb....AppDomai
0000010: 6e2d 636f 6d2e 6f6f 6b6c 612e 7370 6565  n-com.ookla.spee
0000020: 6474 6573 7400 00ff ffff ffff ff41 ed00  dtest........A..
0000030: 0000 0000 005f bc00 0001 f500 0001 f554  ....._.........T
0000040: 3044 1354 3044 1354 2757 c900 0000 0000  0D.T0D.T'W......
0000050: 0000 0000 0000 1d41 7070 446f 6d61 696e  .......AppDomain
0000060: 2d63 6f6d 2e6f 6f6b 6c61 2e73 7065 6564  -com.ookla.speed
0000070: 7465 7374 0007 4c69 6272 6172 79ff ffff  test..Library...
0000080: ffff ff41 ed00 0000 0000 0013 b600 0001  ...A............
0000090: f500 0001 f554 2757 c954 2758 1f54 1b09  .....T'W.T'X.T..
00000a0: df00 0000 0000 0000 0000 0000 1d41 7070  .............App
00000b0: 446f 6d61 696e 2d63 6f6d 2e6f 6f6b 6c61  Domain-com.ookla
...
```

Right. That's some sort of binary file. I can see the app names repeated several times for each app, but we're still going to have to figure out the format.

Luckily for me, the format has already been relatively well reverse engineered[^1]. First, we have a file header, the bytes `mbdb\5\0`. The last two are probably versioning, but so far as I can tell, it hasn't changed. So we'll skip over that for the moment.

Next, we have a sequence of records:


|  Type  |         Name          |                            Note                            |
|--------|-----------------------|------------------------------------------------------------|
| string |        domain         |                  Used for `hash-filename`                  |
| string |         path          |                                                            |
| string |        target         |      Absolute path, only for [[wiki:symlinks]]()      |
| string |       data hash       |                 SHA1 (for encrypted files)                 |
| string |    encryption key     |                                                            |
| uint16 |         mode          |             file/directory/symlink (see below)             |
| uint64 | [[wiki:inode]]() |                                                            |
| uint32 |        user id        |                                                            |
| uint32 |       group id        |                                                            |
| uint32 |     last modified     |                                                            |
| uint32 |     last accessed     |                                                            |
| uint32 |      created at       |                                                            |
| uint64 |       file size       |               0 for symlinks and directories               |
| uint8  | data protection class | 0 if special (link, directory), otherwise ranges from 1-11 |
| uint8  |    property count     |               number of properties following               |


This is then followed by a list of properties:


|  Type  | Name  |            Note            |
|--------|-------|----------------------------|
| string | name  |                            |
| string | value | either UTF8 or binary data |


That sounds pretty straight forward (relatively speaking). Let's write a function to read it. We want to fill out this structure:

```racket
(struct record (domain path hash mode size properties) #:prefab)
(struct property (name value) #:prefab)
```

In general LISP style (so far as I understand it), we will write a series of functions named `read-*`, each of which will read the specified form of data from the current input port. Then, for example, we can have a `read-mbdb` function, which calls `read-record`, which in turn has a bunch of calls to either `read-uint` or `read-string` followed by zero or more calls to `read-property`.

Starting at the outermost layer, lets read an entire file. Specifically, we want a function that will read off those 6 header bytes then continuously read records until the end of the file:

```racket
; Read mdbd records until eof
(define (read-mbdb [in (current-input-port)])
  (read-bytes 6 in)
  (let loop ()
    (cond
      [(eof-object? (peek-char in)) '()]
      [else
       (cons (read-record in) (loop))])))
```

Having that, we need the ability to read an individual record:

```racket
; Read an mbdb record
(define (read-record [in (current-input-port)])

  (define domain (read-string-data in))
  (define path (read-string-data in))
  (define link-target (read-string-data in))
  (define data-hash (read-string-data in))
  (define encryption-key (read-string-data in))

  (define raw-mode (read-uint 2 in))
  (define mode
    (case (arithmetic-shift raw-mode -12)
      [(#xA) (list 'symlink link-target)]
      [(#x8) 'file]
      [(#x4) 'directory]))

  (define inode (read-uint 8 in))
  (define user-id (read-uint 4 in))
  (define group-id (read-uint 4 in))

  (define last-modified (read-uint 4 in))
  (define last-accessed (read-uint 4 in))
  (define created-at (read-uint 4 in))
  (define file-size (read-uint 8 in))

  (define data-protection-class (read-uint 1 in)) ; 0x1 to 0xB
  (define property-count (read-uint 1 in))

  (define properties
    (for/list ([i (in-range property-count)])
      (define name (read-string-data in))
      (define value (read-string-data in))
      (property name value)))

  (define hash (hash-filename path domain))

  (record domain path hash mode file-size properties))
```

Other than the missing functions, one caveat here is the definition of `mode`. I'm not actually sure what's in the other three half bytes, but all we care about is in the first. If it's `A`, it's a symlink. `8` is a file; `4` is a directory. That handles every entry at least on my phone.

Also, you may note that we're not returning all of the data in the records. Honestly, for most of it I just don't need it. It's useful if you're trying to do more interesting things and then write back to the backup, but just to read it? We don't care about user/group ids, et al. It's all there though, with just a tweak. Perhaps I'll figure out a way to pull out the full record if wanted in the future.

Okay, so next, what does it mean to `read-uint`? Well, we're going to have anywhere from 1 to 8 bytes, which we then need to turn into a single value. That's easy enough doing a base conversion (from essentially base 256 to base 10):

```racket
; Read size bytes as a big-endian unsigned integer
(define (read-uint size [in (current-input-port)])
  (define b* (read-bytes size in))
  (for/sum ([i (in-naturals)]
            [b (in-bytes b*)])
    (* (expt 256 (- (bytes-length b*) i 1)) b)))
```

Cool. That means that all that's left is reading strings. Luckily, they have a nice format. Rather than [[wiki:null terminated strings]]() a la C/C++, they store first the length of the string (as a `uint16`) and then that many bytes. There are two caveats though:


* If the size is maxed (`#xFFFF`), it's actually empty
* This same datatype can be either a UTF8 string or raw binary data (try to parse it as a string, fall back to bytes)


Codewise:

```racket
; Read a length + string, if length if #xFFFF the string is empty
; Note: Sometimes 'strings' are actually binary data, return those as bytes
(define (read-string-data [in (current-input-port)])
  (define size (read-uint 2 in))
  (cond
    [(equal? size #xFFFF) ""]
    [else
     (define raw (read-bytes size in))
     (with-handlers ([exn? (λ (_) raw)])
       (bytes->string/utf-8 raw))]))
```

Cool.

```racket
> (with-backup "86b1...aa36"
    (call-with-input-file (build-path (backup-path (current-backup))
                                      "Manifest.mbdb")
      read-mbdb))
'(#s(record "AppDomain-com.ookla.speedtest" "" #f directory 0 ())
  #s(record "AppDomain-com.ookla.speedtest" "Library" "83fee2b4383a3d59c99185862e220d5a0a77d546" directory 0 ())
  #s(record "AppDomain-com.ookla.speedtest" "Library/Preferences" "726b41739d2c95794288f354134f75515db58dbd" directory 0 ())
  #s(record
     "AppDomain-com.ookla.speedtest"
     "Library/Preferences/com.ookla.speedtest.plist"
     "dc4081fac8bf5bdf6ed025d3da24e6b8a287c4fb"
     file
     620
     ())
  #s(record
     "AppDomain-com.ookla.speedtest"
     "Library/Preferences/com.apple.PeoplePicker.plist"
     "f9e644265dbcc0a7179c631e0ba3173868663b04"
     (symlink "/private/var/mobile/Library/Preferences/com.apple.PeoplePicker.plist")
     0
     ())
  ...)
```

It's kind of neat how cleanly binary formats can actually be read at least if they're relatively well documented.

Let's go ahead and add this to the `app` structure and then write a helper as we have before to find a specific app:

```racket
; Load the list of files associated with an app
(define (load-files! app)
  (define app-domain (~a "AppDomain-" (app-name app)))

  (set-app-files!
   app
   (for/list ([record (in-list (list-mdbd-records))]
              #:when (and (equal? (record-domain record) app-domain)
                          (eq? 'file (record-mode record))))
     (file (record-path record)
           (build-path (backup-path (current-backup)) (record-hash record))))))

; Find an app by name (actually a case insensative regex)
; plists and files in domain are loaded when this is called and cached
(define (find-app name)
  (define app
    (for/first ([app (in-list (list-apps))]
                #:when (regexp-match (~a "(?i:" name ")") (app-name app)))
      app))

  ; If this app is missing it's plist / files, load them
  (when (and app (not (app-plist app))) (load-plist! app))
  (when (and app (not (app-files app))) (load-files! app))

  app)
```

Yes, this does has the disadvantage that if you just `list-apps`, you won't get the plists and file lists. On the flip side though, this one uses a regex, so you can just search by app name. Most developers (although not all I've found) will include that as part of their internal name. They take a bit to load though, especially if you have a lot of apps, so I think that's a fair enough trade off. It's still caching `Manifest.mbdb` though, so at least that only has to be read once:


```racket
(define mdbd-records-by-backup (make-hash))
(hash-set! mdbd-records-by-backup #f '())

; Get all MDBD records
(define (list-mdbd-records)
  (hash-ref!
   mdbd-records-by-backup
   (current-backup)
   (λ ()
     (call-with-input-file (build-path (backup-path (current-backup))
                                       "Manifest.mbdb")
       read-mbdb))))
```

Once you start digging through these lists, there are some pretty interesting files ... but that will have to wait for another post. This one is already pretty long. I think I'll have at least one more post in this series taking everything I've done thus far and turning it into an actual backup solution. Keep an eye out!

The full source thus far (and I've finally caught up) is on GitHub: <a href="https://github.com/jpverkamp/ios-backup">ios-backup</a>.

If you've installed `ios-backup` as a library, you can import these new functions with `(require ios-backup/apps)` or if you really want to get adventerous `(require ios-backup/mbdb)`.

Here is a list of all of the posts in this series:

{{< taxonomy-list "series" "iOS Backups in Racket" >}}

[^1]: initial source: <a href="https://code.google.com/p/iphonebackupbrowser/wiki/MbdbMbdxFormat">iphonebackupbrowser</a>, although some of the details came from elsewhere
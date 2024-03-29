---
title: 'Adventures in Racket: gzip'
date: 2013-08-06 15:00:10
programming/languages:
- Racket
- Scheme
programming/topics:
- Compression
- Gzip
---
In my research, I work with a lot of rather large text files--on the order of gigabytes if not terabytes per file. Since they're plain text, they're generally rather compressible though, so it makes sense to `gzip` them while they're on disk. The drawback though comes when you're working with them. There are a few options though.

<!--more-->

First, you could `gunzip` the files before use and `gzip` them again when you're done:

```bash
gunzip data.txt.gz
analyze data.txt
gzip -9 data.txt
```

It's simple, it's straight forward, but it requires a heck of a lot more disk space. Even if you only do one file at a time, you still need to have at least enough to deal with the files. In addition, if you could possibly bail out early when dealing with the file, you can't here. You'll have to decompress the entire file, then re-compress it in turn.

The next option would be to use your Unix-fu:`gunzip` it into a pipe then directly into the program, something like this:

```bash
gunzip -c data.txt.gz > analyze
```

It has the same advantages of the previous form in that it's easy to deal with, but we lose a bit of flexibility. For example, what if we want to process more than one file?

```bash
gunzip -c data.*.txt.gz > analyze
```

This works, but we lose the delineation between files. If that's important, this is a no go. Also, we still have to decode the entire file.

Okay, so what about to do it directly in the script? Traditionally, I write a lot of scripts in Python. It's quick and generally painless to write and I know the language particularly well. If I wanted to process gzipped files, all I would need is something like this:

```python
import gzip
with gzip.open('data.txt.gz', 'r') as fin:
    for line in fin:
         print(line)
```

Quick and easy. In addition, `gzip.open` returns a file-like object that's only read as we need it. That way, we can only have (roughly) one line in memory at a time. That's exactly what I want when dealing with large files.

More recently though though, I've been writing a lot of scripts in Racket. For slightly more in depth scripts, it has a lot going for it. Racket is{{< doc racket "batteries included" >}}, nicely functional[^1], and can be much more parallelized to multi-core machines without running into Python's pesky [[wiki:Global Interpreter Lock]]()[^2].

So how can we write the same code in Racket?

Unfortunately, it's not quite as easy. There is{{< doc racket "file/unzip" >}}module, but it doesn't really have a nice `with-input-from-gzipped-file` or `with-gunzip` function. The closest thing we have appears to be `gunzip-through-ports`. It takes two ports,`in` and `out`, reading gzipped data from`in`and writing decompressed data to `out`. But how do we make use of that?

It took me a while to find what I was looking for, but finally I came across{{< doc racket "pipes" >}}. They're essentially equivalent to Unix-like pipes[^3], forming a sort of bridge between two streams. So theoretically, we can open the file, use `gunzip-through-ports` to attach it to the pipe, and then read from the other end. Something like this:

```scheme
(define (with-gunzip thunk)
 (define-values (pipe-from pipe-to) (make-pipe))
 (gunzip-through-ports (current-input-port) pipe-to)
  (parameterize ([current-input-port pipe-from])
    (thunk))
 (thunk))
```

Parameterize will allow us to redirect the `current-input-port` and automatically set it back when we're done, even if we bail out with an error.

To use it, we would write code like this:

```scheme
(with-input-from-file "data.txt.gz"
  (λ ()
    (with-gunzip
      (λ ()
        (for ([i (in-naturals)]
              [line (in-lines)])
          (printf "line ~a: ~a\n" i line))))))
```

It actually works pretty well, but unfortunately it doesn't work entirely. There are at least three issues that we're going to want to deal with:


* It doesn't terminate; once the file has been read it hangs in `in-lines`
* It doesn't close the ports; if you try to use the same file, you'll get an error
* There's no error handling; ugly things happen if you pass it a non-gzipped stream for example
* There's no buffering; the entire file is gunzipped in memory (if possible)


Let's take each one in order.

First, we have termination. Based on <a href="http://lists.racket-lang.org/users/archive/2013-August/058852.html">a response from Ryan Culpepper</a> on the Racket mailing list, the problem is that `gunzip-through-ports` doesn't actually close the port. This means that an `eof-object?` is never sent through the `pipe` to `in-lines`.

So at some point we need to close the port. The problem is: when? If we close it at the end as one might expect, it won't work. Since the code hangs in the `for`, we'll never get to it. So we have to have it before that at least. Let's true putting it right after the `gunzip-through-ports` line[^4]:

```scheme
(define (with-gunzip thunk)
  (define-values (pipe-from pipe-to) (make-pipe))
  (gunzip-through-ports (current-input-port) pipe-to)
  (close-output-port pipe-to)
  (parameterize ([current-input-port pipe-from])
    (thunk))
  (close-input-port pipe-from))
```

It turns out, this actually works perfectly. It was counter intuitive to me at first, but then I ran some timing tests. It turns out that the `pipe` and `gunzip-through-ports` aren't actually buffering anything. On the latter call, everything that was on `current-input-port` is gunzipped and written through `pipe-to` to `pipe-from`. So we can go ahead and close `pipe-to` right then. Better yet, we've actually finished the second point as well. Everything should now be closed by the time `with-gunzip` exits.

This leads us directly to the third problem though. What do we do if we have an error? Since control bails out, the ports will never be closed. Let's check out Racket's {{< doc racket "exception model" >}}.

Theoretically, we're looking for `with-handlers` looking specifically for a `exn:fail?` condition (the one raised internally by `error`). Something like this should do what we need:

```scheme
(define (with-gunzip thunk)
  (define-values (pipe-from pipe-to) (make-pipe))
  (with-handlers ([exn:fail?
                   (λ (err)
                     (close-output-port pipe-to)
                     (close-input-port pipe-from)
                     (raise err))])
    (gunzip-through-ports (current-input-port) pipe-to)
    (close-output-port pipe-to)
    (parameterize ([current-input-port pipe-from])
      (thunk))
    (close-input-port pipe-from)))
```

~~This way, we close the two ports and then pass along the error. Originally, I just used `(raise err)`, but that revealed the guts of my function. I don't mind if people go looking, but I don't want that to be necessary. Using `exn-message` allows us to pass along the message but not the original error. So if we try do do this:~~

**Edit 6 Aug 13:**: Based on <a href="http://lists.racket-lang.org/users/archive/2013-August/058858.html">this message from Robby Findler</a>, `raise` is the better option since it will preserve the stack trace into the code I'm using. Plus it's cleaner. Mostly, I got confused when originally using `raise` since the error didn't appear to be caught (since of course I was re-raising the original).

```scheme
(with-input-from-file "not-gzipped.txt"
  (λ ()
    (with-gunzip
      (λ ()
        ...))))
```

We'll get this error:

```
<span style="color: red;">with-gunzip: gnu-unzip: bad header</span>
```

It looks a bit strange with the nested colons, but it gives us exactly what we want. Better yet, the ports are correctly being closed.

All that leaves us is buffering. Originally, my biggest problem with this code was that it read the entire file into memory at once. With files in the tens of gigabytes, that could be a problem... So how do we fix it? <a href="http://lists.racket-lang.org/users/archive/2013-August/058852.html">Mailing list</a> to the rescue once again! Essentially, I missed an optional argument to `make-pipe`. If you pass `#f` (the default), there's no buffer. But instead, you can pass an `exact-positive-integer?` which will be the buffer size in bytes.

We don't necessary want to assume that the user either wants buffering or wants a certain size, so we'll make it configurable. Quick and easy:

```scheme
(define (with-gunzip thunk #:buffer-size [buffer-size #f])
  (define-values (pipe-from pipe-to) (make-pipe buffer-size))
  (with-handlers ([exn:fail?
                   (λ (err)
                     (close-output-port pipe-to)
                     (close-input-port pipe-from)
                     (raise err))])
    (gunzip-through-ports (current-input-port) pipe-to)
    (close-output-port pipe-to)
    (parameterize ([current-input-port pipe-from])
      (thunk))
    (close-input-port pipe-from)))
```

It's starting to get a bit more complicated, but it works great. If we want a buffer of 1 megabyte:

```scheme
(with-input-from-file "data.txt.gz"
  (λ ()
    (with-gunzip
      (λ ()
        (for ([i (in-naturals)]
              [line (in-lines)])
          (printf "line ~a: ~a\n" i line)))
      #:buffer-size (* 1024 1024))))
```

There is one problem though, the user can pass absolutely anything to `#:buffer-size`. Let's use a Racket feature I probably don't take as much advantage of as I probably should: {{< doc racket "contracts" >}}. Essentially, they work like [[wiki:Type signature|type signatures]](). It looks a little ugly, but they're fairly easy to work with:

```scheme
(provide/contract
 (with-gunzip
   (->* ((-> any))
        (#:buffer-size (or/c false? exact-positive-integer?))
        any)))
```

Breaking this apart, we have a function (`->*`, the `*` signifies optional parameters) which tasks a required thunk--`(-> any)`, required because it's in the first list--and an optional (because it's in the second list) keyword (`#:...`) parameter that's either `false?` or the same `exact-positive-integer?` that `make-pipe` is expecting>. After all that, we'll return some generic data value (`any`). This way, we can't do this:

```scheme
> (with-gunzip (λ () (read)) #:buffer-size 'frog)
```

```
<span style="color: red;">with-gunzip: contract violation
  expected: (or/c false? exact-positive-integer?)
  given: 'frog</span>
```

Exactly what we wanted!

Well, that's almost it. One thing we can still do is write a parallel `with-gzip` function. We'll use `#f` to ignore the filename and the current system time for timestamp (since gzipped files require those), but other than that, everything is pretty much exactly the same:

```scheme
(provide/contract
 (with-gzip
  (-> (-> any) #:buffer-size [or/c false? exact-positive-integer?] any)))

(define (with-gzip thunk #:buffer-size [buffer-size #f])
  (define-values (pipe-from pipe-to) (make-pipe buffer-size))
  (with-handlers ([exn:fail?
                   (λ (err)
                     (close-output-port pipe-to)
                     (close-input-port pipe-from)
                     (raise err))])
    (gzip-through-ports (current-input-port) pipe-to #f (current-seconds))
    (close-output-port pipe-to)
    (parameterize ([current-input-port pipe-from])
      (thunk))
    (close-input-port pipe-from)))
```

We can test it by using both in sequence:

```scheme
(define input "This is a test: The duck quacks at midnight...")

(printf "input: ~s\n" input)

(define gzipped
  (with-output-to-bytes
   (λ ()
     (with-input-from-string input
      (λ ()
        (with-gzip
         (λ ()
           (display (port->bytes (current-input-port))))))))))

(printf "gzipped: ~s\n" gzipped)

(define gunzipped
  (with-output-to-string
   (λ ()
     (with-input-from-bytes gzipped
      (λ ()
        (with-gunzip
         (λ ()
           (display (port->string (current-input-port))))))))))

(printf "gunzipped: ~s\n" gunzipped)
```

The test is a but contrived and the nested thunks are a bit ugly, but it works:

```text
input: "This is a test: The duck quacks at midnight..."
gzipped: #"\37\213\b\0\336u\0R\0\3\v\311\310,V\0\242D\205\222\324\342\22+\205\220\214T\205\224\322\344l\205\302\322\304\344l\240x\211BnfJ^fzF\211\236\236\36\0G7\244\232.\0\0\0"
gunzipped: "This is a test: The duck quacks at midnight..."
```

Good to go!

Eventually, I'll put it on PLaneT, but for now it's available on GitHub: <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/with-gzip.rkt">with-gzip</a>

**Edit 6 Aug 2013:** Robby Findler had <a href="http://lists.racket-lang.org/users/archive/2013-August/058858.html">another suggestion</a> on the mailing list: rather than using `with-handlers`, try `dynamic-wind`. Essentially, `dynamic-wind` takes three thunks: pre, value, and post. It will call the pre-thunk when control is passed to it, then the value-thunk, then the post-thunk, returning whatever the value-thunk would have. The best part though is that if control exits for other reasons (say, an error), post-thunk will still be called. This way we can handle errors without error handling. If we wanted to turn that into code, we have something like this:

```scheme
(define (with-gunzip thunk #:buffer-size [buffer-size #f])
  (define-values (pipe-from pipe-to) (make-pipe buffer-size))
  (dynamic-wind
   void
   (λ ()
     (thread
      (λ ()
        (gunzip-through-ports (current-input-port) pipe-to)
        (close-output-port pipe-to)))
     (parameterize ([current-input-port pipe-from])
       (thunk)))
   (λ ()
     (unless (port-closed? pipe-to) (close-output-port pipe-to))
     (unless (port-closed? pipe-from) (close-input-port pipe-from)))))
```

It's nice and clean, even correctly dealing with closing the pipe whether or not things work correctly. The `thread` there helps with reading. Without it, `gunzip-through-ports` will block, depending on how much it is trying to read. This way, it can run in parallel as needed.

[^1]: Yes, I know I *can* write functional code in Python. I often do. It's just more natural in Racket
[^2]: Using{{< doc racket "places" >}};{{< doc racket "threads" >}}run in a single OS thread and thus have the same problem
[^3]: Although they're implented without them
[^4]: While we're at it, we'll go ahead and close `pipe-from` as well

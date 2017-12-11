---
title: Extending Racket structs to bitfields
date: 2013-09-23 14:00:09
programming/languages:
- Racket
- Scheme
programming/topics:
- Bitfields
- Data Structures
---
Keen eyed observers may have noticed that last Friday when I [posted about converting]({{< ref "2013-09-20-deploy-racket-libraries-to-planet-2.md" >}}) my various Racket libraries to Planet 2 packages, that there was a new package there I haven't otherwise talked about: <a href="http://racket.jverkamp.com/bit-struct/">bit-struct</a>. Today seems like a good time to talk about that. Theoretically, I'll also have another post or two this week showing exactly what I'm doing with it (spoilers: it involves sending on the order of billions of DNS requests[^1]).

<!--more-->

If you'd like to go straight to the code, it's available on GitHub: <a href="https://github.com/jpverkamp/bit-struct">jpverkamp/bit-struct</a>. Along with the new Planet 2 packages, I also have documentation now, available here: <a href="http://racket.jverkamp.com/bit-struct/">bit-struct documentation</a>.

The basic idea is we want to take straight forward Racket structs (already rather useful in their own right), limit them to only numeric values, and extend them to convert the structs to bit fields (as Racket {{< doc racket "bytes" >}}) and back. In theory[^2], this will allow interaction with systems that have very specific memory layouts, such as networking packets. As a bit of a spoiler, this should be both completely valid and do exactly what you might expect[^3]:

```scheme
(define-bit-struct dns
  ([id      16]
   [qr      1]  [opcode  4]  [aa      1]  [tc      1]  [rd      1]
   [ra      1]  [z       3]  [rcode   4]
   [qdcount 16]
   [ancount 16]
   [nscount 16]
   [arcount 16]
   [data    _]))
```

The extra advantage in this case is that (via the magic of macros) three additional functions are also defined:


* `(build-dns #:key val ...)` - take any number of keyword arguments matching the struct fields above and create the struct, any unspecified values are set to 0
* `(dns->bytes data)` - convert a struct into a bit field, using the given bit widths
* `(bytes->dns buffer)` - convert a bit field back into a struct, again using the bit widths


Here are some more examples:

```scheme
> (define packet
    (build-dns
     #:id (random 65536)
     #:tc 1
     #:qdcount 1
     #:data
     (bytes-append
      #"\3www\6google\3com\0"
      (bytes 0 1)
      (bytes 0 1))))
> packet
(dns 3202 0 0 0 1 0 0 0 0 1 0 0 0 #"\3www\6google\3com\0\0\1\0\1")
> (dns->bytes packet)
#"\f\202\2\0\0\1\0\0\0\0\0\0\3www\6google\3com\0\0\1\0\1"
> (bytes->dns (dns->bytes packet))
(dns 3202 0 0 0 1 0 0 0 0 1 0 0 0 #"\3www\6google\3com\0\0\1\0\1")
```

Nice and straight forward. The real question though is what sort of magic did we need to get this all working? Just as useful as having the package itself is the additional experience with a relative complicated macro.

First, we need to introduce some more names. Normally, that isn't particularly straight forward, since we have to bend the rules of {{< wikipedia page="Hygienic macro" text="hygienic macros" >}} just a bit. Luckily though, Racket provides the tools to do just that: {{< doc racket "with-syntax" >}} and {{< doc racket "format-id" >}}. Essentially, `with-syntax` is similar to `syntax-case` in that it binds more syntax variables. `format-id` is basically an extension to format that attaches scope to the new `id` in order to make cleaner error message. Always a plus. :smile: Here's how all of that looks:

```scheme
; Bind a struct (and normal functions) plus these new functions:
; build-* takes keyword arguments for parameters (default = 0)
; *->bytes turns a struct into bytes
; bytes->* takes bytes and returns a struct
(define-syntax (define-bit-struct stx)
  (syntax-case stx ()
    [(_ struct-name ([name* bits*] ...))
     ; Get some identifiers we'll need
     (with-syntax ([builder-name (format-id stx "build-~a" #'struct-name)]
                   [bytes->-name (format-id stx "bytes->~a" #'struct-name)]
                   [->bytes-name (format-id stx "~a->bytes" #'struct-name)])
       ...)]))
```

More or less straight forward. It does require <a href="http://docs.racket-lang.org/reference/stx-patterns.html?q=with-syntax#(form._((lib._racket/private/stxcase-scheme..rkt)._syntax-case))" data-pltdoc="x">syntax-<wbr />case</a> rather than <a href="http://docs.racket-lang.org/reference/stx-patterns.html?q=with-syntax#(form._((lib._racket/private/stxcase-scheme..rkt)._syntax-rules))" data-pltdoc="x">syntax-<wbr />rules</a> which I normally use (in order to have access to the raw `stx` to pass to `format-id`, but other than that, a pretty normal macro. Now each function in turn.

First, `build-*`. This one does the magic of creating a function with dynamic keyword parameters that match whatever fields the struct has. To do that, we need the function {{< doc racket "make-keyword-procedure" >}}, which takes a procedure of the form `((Listof keys) (Listof values) any ... . -> . any)`. So if you define a function `(λ (keys vals . args) ...)`, keys and values are lists of the same length, the first containing the keywords and the latter containing the associated values. You could easily make it into an association list if you wanted just by calling `(map list keys vals)` (or with `for` as I did below). I did have to convert them though. As given, they are keywords but I wanted symbols. I'm not sure there's a direct way to convert between those two, but it's easy enough via an intermediate string.

In this case, I'm ignoring the `rest` parameter so only keyword parameters are allowed.

```scheme
; Create the builder function
(define builder-name
  (make-keyword-procedure
   (λ (keys vals)
      ; Create an association map from the new values
      (define new-values
        (for/list ([k (in-list (map string->symbol 
                                    (map keyword->string keys)))]
                   [v (in-list vals)])
          (list k v)))

      ; Build a new structure
      (apply 
       maker-name
       (for/list ([name (in-list '(name* ...))]
                  [bits (in-list '(bits* ...))])
         (cond
           [(assoc name new-values)
            => (λ (kv) (second kv))]
           [(eq? bits '_) #""]
           [else            0]))))))
```

After we have that association list, we'll use a second loop to create the structure. Since we're inside of the macro, `'(name* ...)` expands to a list of whatever was in the first position for each argument when `define-bit-struct` was called. Likewise, bits is a list of the bit widths. With all of that, we can loop across these values. Another neat trick in this code is the use of `=>` in the `cond`. Essentially, `assoc` will take the association list we created and query it. If the key is there, it will call the given function, passing the key/value pair as an argument (`kv`). If it's not there, use the `else` case to set the value to 0.

```scheme
; Create the parser function
(define (bytes->-name buffer)
  ; Set names with parameters (easier than making lots of ids)
  (define name* (make-parameter 0)) ...
  ; Unpack fields into those parameters as integers
  ; _ is different, it stores any remaining bytes
  (define _
    (for/fold ([offset 0])
              ([name (in-list (list name* ...))]
               [bits (in-list '(bits* ...))])
      (cond
        [(number? bits)
         (name (extract-bytes buffer offset (+ offset bits)))
         (+ offset bits)]
        [else
         (name (subbytes buffer (quotient offset 8)))
         offset])))
  ; Create the structure
  (apply 
   maker-name
   (for/list ([name (list name* ...)])
     (name))))
```

For the second function, we want to be able to take a sequence of bytes and pull one of these structures out of it. If we need to get only part of a byte or extend over multiple bytes (both of which happen in the DNS example), the function `extract-bytes` will do just that:

```scheme
; Extract bits from a bit field
(define (extract-bytes buffer from [to #f])
  ; Extract the bytes we're interested in
  (define f (quotient from 8))
  (define t (if to 
                (let ([q (quotient to 8)])
                  (if (zero? (remainder to 8)) q (+ 1 q)))
                (bytes-length buffer)))
  (define chunk (subbytes buffer f t))
  ; Convert to a base 256 number
  (define numeric
    (for/fold ([total 0])
              ([byte (in-bytes chunk)])
      (+ byte (* total 256))))
  ; Shift off the ends
  (bitwise-and
   (arithmetic-shift numeric 
                     (if to 
                         (let ([r (remainder to 8)])
                           (if (zero? r) r (- r 8)))
                         0))
   (- (arithmetic-shift 1 (- to from)) 1)))
```

First, we get just the bytes we're interested in as a list. Then, we convert that to a single number by treating the list as a 'base 256' number. Finally, we use an `arithmetic-shift` to pull off bits at one end and a `bitwise-and` with a mask to select only the ones from the other end that we want. The bit twiddling gets a bit complicated here, but once it all works, you don't have to think about it any more--just use it.

```scheme
; Create the ->bytes function
(define (->bytes-name data-struct)
  (define data (struct->vector data-struct))
  (let loop ([bits '(bits* ...)]
             [buffer 0]
             [buffer-bits 0]
             [index 1])
    (cond
      ; Full buffer, transfer it
      [(and (> buffer-bits 0) (zero? (remainder buffer-bits 8)))
       (bytes-append
        (number->bytes buffer (quotient buffer-bits 8))
        (loop bits 0 0 index))]
      ; Nothing left
      [(null? bits)
       #""]
      ; Current value is bytes, copy directly
      [(eq? (first bits) '_)
       (bytes-append
        (vector-ref data index)
        (loop (rest bits) buffer buffer-bits (+ index 1)))]
      ; Otherwise, add to buffer
      [else
       (loop
        (rest bits)
        (+ (* buffer (arithmetic-shift 1 (first bits)))
           (vector-ref data index))
        (+ buffer-bits (first bits))
        (+ index 1))])))
```

The third and final function's code is actually fairly similar, in that it has to loop over the names/bit widths. One additional part that it does is that it uses a `named let` to collect the current offset within a byte. That way we collect partial bytes in a `buffer` until we have some multiple of 8. Then we use the dual to `extract-bytes` (`number->`) to convert back to bytes. 

And that's all there is to it. It's certainly not bullet proof just yet (for example, I know that negative values will probably do strange things to it, as will providing keywords that don't exist to `build-*`), but it's certainly a good first step. It should be useful later this week.

As always, today's code is available on GitHub: <a href="https://github.com/jpverkamp/bit-struct">jpverkamp/bit-struct</a>. This time, there's also documentation available here: <a href="http://racket.jverkamp.com/bit-struct/">bit-struct documentation</a>.

[^1]: Not to DoSing anyone though (at least not on purpose)
[^2]: In practice as well actually; we'll see that later this week
[^3]: If what you expect is a struct with the given names and ordered fields each containing the given number of bits
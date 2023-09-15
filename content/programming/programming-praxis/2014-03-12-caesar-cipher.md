---
title: Caesar cipher
date: 2014-03-12 14:00:10
programming/languages:
- Racket
- Scheme
programming/sources:
- Programming Praxis
programming/topics:
- Cryptography
---
<a href="http://programmingpraxis.com/2014/03/11/caesar-cipher/">Here's</a> a 5 minute[^1] coding challenge from Programming Praxis:

> A [[wiki:Caesar cipher|caeser cipher]](), named after Julius Caesar, who either invented the cipher or was an early user of it, is a simple substitution cipher in which letters are substituted at a fixed distance along the alphabet, which cycles; children’s magic decoder rings implement a caesar cipher. Non-alphabetic characters are passed unchanged. For instance, the plaintext PROGRAMMINGPRAXIS is rendered as the ciphertext SURJUDPPLQJSUDALV with a shift of 3 positions.

{{< figure src="/embeds/2014/caesar-shift.png" >}}
-- Source: [[wiki:File:Caesar cipher left shift of 3.svg|Wikipedia]](), public domain

<!--more-->

To make it a bit more interesting, I'm actually going to be using a different `#lang` built on Racket: <a href="https://github.com/greghendershott/rackjure">rackjure</a>. If you're running a newer version of Racket (6+), you can install it with either `raco pkg install rackjure` or with the Package Manger built into DrRacket. Then just change the `#lang` line at the top of your file to `#lang rackjure`.

What specifically do I want from Rackjure? The threading macro `~>`. Basically, it takes a value and 'threads' it as the first argument through a series of functions. The example on the <a href="https://github.com/greghendershott/rackjure">Rackjure GitHub page</a>: 

```scheme
> (string->bytes/utf-8 (number->string (bytes-length #"foobar") 16))
#"6"

> (~> #"foobar"
      bytes-length
      (number->string 16)
      string->bytes/utf-8)
#"6"
```

In our case, we want it because we're going to do run through a similar stream of transformations on each character:


* Convert from a character to a number using {{< doc racket "char->integer" >}}
* Get to a zero based system by subtracting `#\A = 65`
* Add/subtract the offset for this particular Caesar cipher
* Get the [[wiki:Modulo operation|modulus 26]]() so we have a letter when we're done
* Get back to a letter by adding `#\A = 65` back on
* Convert back to a character with {{< doc racket "integer->char" >}}


Turn that into Rackjure:

```scheme
(define (caesar str n)
  (define A (char->integer #\A))
  (list->string
   (for/list ([c (in-string str)])
     (~> c char->integer (- A) (+ n) (mod 26) (+ A) integer->char))))
```

If we didn't have `~>`, that would look something more like this:

```scheme
(define (caesar str n)
  (define A (char->integer #\A))
  (list->string
   (for/list ([c (in-string str)])
     (integer->char (+ (mod (+ (- (char->integer c) A) n) 26) A)))))
```

I'll leave it up to you which of the two styles you think is easier to read--either the Scheme style inside out, jumping back and forth between the operators and their arguments or the Clojure style left to right[^2].

Unfortunately, Racket doesn't have a `mod` function built in[^3]. You can get one from R6RS though:

```scheme
(require (only-in rnrs/base-6 mod))
```

And there you have it. Simple (and almost trivial to crack) encryption:

```scheme
> (caesar "HELLOWORLD" 10)
"ROVVYGYBVN"
> (caesar "ROVVYGYBVN" -10)
"HELLOWORLD"
```

We can make it at least a little better though. Let's go ahead and deal with lower case and non-alphabetic characters:

```scheme
(define (caesar str n)
  (define A (char->integer #\A))
  (define a (char->integer #\a))
  (list->string
   (for/list ([c (in-string str)])
     (cond
       [(char<=? #\A c #\Z)
        (~> c char->integer (- A) (+ n) (mod 26) (+ A) integer->char)]
       [(char<=? #\a c #\z)
        (~> c char->integer (- a) (+ n) (mod 26) (+ a) integer->char)]
       [else
        c]))))
```

Basically, the only thing that changes is the offset. For upper case letters, we use `#\A = 65`, for lower case `#\a = 97`. Anything that's not a letter? We just leave it alone. 

How's it work?

```scheme
> (caesar "Hello world!" 100)
"Dahhk sknhz!"
> (caesar "Dahhk sknhz!" -100)
"Hello world!"
```

It's actually such a simple program, you have all of the code right there, but just in case you can also download it from GitHub: <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/caesar-cipher.rkt">caesar-cipher.rkt</a>

[^1]: More or less
[^2]: Exercise to the reader: which do you think I prefer?
[^3]: At least not one that deals how we need with negative numbers
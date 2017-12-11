---
title: Numbers as words in arbitrary bases
date: 2013-02-06 23:00:10
programming/languages:
- Racket
- Scheme
programming/sources:
- Daily Programmer
programming/topics:
- Dictionary
- Word Games
---
<a href="http://www.reddit.com/r/dailyprogrammer/comments/17zn6g/020613_challenge_120_intermediate_base_conversion/" title="Challenge #120 [Intermediate] Base Conversion Words">Today's intermediate challenge</a> on Reddit's /r/dailyprogrammer intrigued me somewhat, so I decided to take a crack at it. The basic idea is if you are given a number, try converting it to all bases from 2 to 64 (with a special encoding). Print out any of those that are words.

For example, if you interpret the number 44,269 as a {{< wikipedia page="Hexadecimal" text="base 16 (Hexadecimal)" >}} number, you get the word "aced". So just how many of these words are there out there?

<!--more-->

The first thing we want is the ability to associate a character with a given value. Since we want 64 possible values, we need case sensitive strings (so "a" is distinct from "A"). But that only gives us 62 (10 digits, 26 lower case letters, and 26 upper case letters), so we'll also add + and /. It's the same character set as {{< wikipedia page="Base64" text="Base64 encoding" >}}, but a different ordering.

```scheme
; order of characters for the encoding
(define encoding
  (string-append
   "0123456789"
   "abcdefghijklmnopqrstuvwxyz"
   "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
   "+/"))

; convert a number into a character
(define n->c
  (for/hash ([i (in-naturals)]
             [c (in-string encoding)])
    (values i c)))

; convert a character into a number
(define c->n
  (for/hash ([i (in-naturals)]
             [c (in-string encoding)])
    (values c i)))
```

Here we create a {{< doc racket "Racket hash table" >}} associating each number with its character (`n->c`) and then each character to its numerical value (`c->n`).

Once that's been done, we want to be able to convert between lists of digits and strings of characters. For example if we have the string `"101"` that would be `'(1 0 1)`. Likewise `"abc"` would be `'(10 11 12)`.

```scheme
; convert a list of digits in decimal form into a string
(define (dlist->string dls)
  (list->string
   (for/list ([n (in-list dls)])
     (hash-ref n->c n))))

; convert a string into a list of digits in decimal form
(define (string->dlist str)
  (for/list ([c (in-string str)])
    (hash-ref c->n c)))
```

This just directly uses those hashes we created earlier. Technically `dlist->string` could instead directly `string-ref` into `encoding` but I like the parallelism of doing it this way.

Next, we want to be able to convert some arbitrary decimal list to/from a number. This should (theoretically) be covered in most introductory CS courses (at least for a few limited bases) so if this code isn't familiar, take a deeper look. This is the recursive way to do it, but it's close enough to the iterative algorithm that you should be able to convert them.

```scheme
; convert a digit list in base b to number
(define (->decimal dls b)
  (let loop ([dls dls] [n 0])
    (cond
      [(null? dls) n]
      [else
       (loop (cdr dls) (+ (* n b) (car dls)))])))

; convert a decimal number to a digital list in base b
(define (decimal-> n b)
  (let loop ([n n] [dls '()])
    (cond
      [(= n 0) dls]
      [else
       (loop (quotient n b) (cons (remainder n b) dls))])))
```

We're just about there. The next thing we want to be able to do is get strings of all of the bases from a given number. Something like this:

```scheme
; get all basis conversions for a number
(define (->all-bases n)
  (for/list ([b (in-range 2 65)])
    (dlist->string (decimal-> n b))))
```

So if you take {{< wikipedia page="867-5309/Jenny" text="Jenny's number" >}}:

```scheme
> (->all-bases 8675309)
'("100001000101111111101101" "121022202021202" "201011333231" "4210102214"
  "505535245" "133511306" "41057755" "17282252" "8675309" "4995985"
  "2aa4525" "1a49926" "121b7ad" "b656de" "845fed" "61ed65" "4ab9bb"
  "39af64" "2e4859" "22cfik" "1f0g45" "1800a8" "123d75" "m55c9" "ipf7j"
  "g8k7k" "e35cd" "c7kdh" "al96t" "9c6bl" "88nvd" "7ada5" "6gok5" "5rbuy"
  "55xwt" "4n9zu" "463vn" "3t9qw" "3fm2t" "32zwB" "2x3EF" "2n4Cg" "2dB25"
  "2594t" "1H5Dv" "1Aqc2" "1ulft" "1oAa6" "1jk69" "1ekj5" "19AgJ" "15el4"
  "1153L" "Q7LN" "Nmkd" "KM8n" "IqOh" "Geb8" "E9Mt" "Cdrb" "AoQl" "yHMk"
  "x5/J")
```

Then you can filter those using my [dictionary library]({{< ref "2012-10-11-dictionary-tries-in-racket.md" >}}):

```scheme
; get a list of all bases that are also words
(define (->all-base-words dict n)
  (filter
   (lambda (word) (contains? dict word))
   (->all-bases n)))
```

There aren't any in Jenny's number, but there are actually two in the example I gave earlier:

```scheme
> (->all-base-words dict 8675309)
'()

> (->all-base-words dict 44269)
'("aced" "fEe")
```

(The dictionary is case-insensitive while the words are case-sensitive, so you get some funny looking words like `"fEe"`.)

Finally, as a bonus solution, here's a nice infinite stream of all possible words as a CSV file:

```scheme
; scan for numbers that turn into words
(define (scan dict)
  (for ([i (in-naturals)])
    (for ([b (in-range 2 65)]
          [word (in-list (->all-bases i))])
      (when (contains? dict word)
        (printf "~s,~s,~s\n" i b word)))))
```

And here's an arbitrary slice:

```scheme
...
56672,47,"puB"
56673,60,"fIx"
56674,47,"puD"
56674,51,"lEd"
56674,64,"dRy"
56675,51,"lEe"
56677,39,"Baa"
56677,45,"rIm"
56677,47,"puG"
56677,51,"lEg"
56677,60,"fIB"
56679,51,"lEi"
56680,39,"Bad"
56680,45,"rIp"
56680,60,"fIE"
56681,51,"lEk"
56682,60,"fIG"
56682,61,"fed"
56682,62,"eKe"
56683,39,"Bag"
56683,61,"fee"
56684,39,"Bah"
56684,43,"usa"
56685,51,"lEo"
...
```

If you'd like to try it out, you can download the entire source from my GitHub:
- <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/base-conversion-words.rkt" title="Base Conversion Words source on GitHub">Base Conversion Words source</a>
- <a herf="https://github.com/jpverkamp/small-projects/blob/master/racket-libraries/dictionary.rkt" title="Racket Dictionary library source on GitHub">Racket Dictionary library source</a>

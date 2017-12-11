---
title: Number words
date: 2014-08-13 14:00:55
programming/languages:
- Racket
- Scheme
programming/sources:
- Programming Praxis
programming/topics:
- Regular Expressions
- Word Games
---
Today's five minute post brought to you via <a href="http://programmingpraxis.com/2014/07/25/number-words/">Programming Praxis</a> / <a href="http://www.careercup.com/question?id=5120347909128192">Career Cup</a>:


> Given a positive integer, return all the ways that the integer can be represented by letters using the mapping 1 -> A, 2 -> B, …, 26 -> Z. For instance, the number 1234 can be represented by the words ABCD, AWD and LCD.


<!--more-->

That may look fairly straight forward. Basically, it's a {{< wikipedia "parsing" >}}/{{< wikipedia "lexing" >}} problem. You take a string as input and break it into a series of tokens (in this case, numbers 1-26); then each token is converted into a letter.

Unfortunately, it's a bit more complicated than that, since the grammar is ambiguous. Taking the example `1234` from above, should you parse that as `1 2 3 4 = ABCD`? Or what about `1 23 4 = AWD`? Or even `12 3 4 = LCD`? In a nutshell, we have to do all of them. So we want some sort of branching lexer that will try all possible routes.

So let's start with a function that meta-function that can make such a parser:

```scheme
; Make an optional parser
; If the regex matches, add it to each possible next parse
; If it does not, return an empty list (to be appendable)
(define (make-parser re)
  (λ (str)
    (match str
      [(regexp re (list _ n rest))
       (map (curry ~a (n->char n)) (number->words rest))]
      [any
       '()])))
```

Looks a bit funny, (especially since we haven't defined `number-&gt;words` yet), but basically we try to match the regular expression. If that works, make the recursive call (to `number-&gt;words`) and then append that string (as a character via `n->char`) to each recursive result. If there are no recursive results, this `map` will return an empty list. Likewise, if the regular expression doesn't match.

Next step, write the two parsers. We want to parse either a single digit number or a two digit number:

```scheme
; Create parsers for valid 1 digit and 2 digit letter numbers
(define parse-1 (make-parser #px"([1-9])(.*)"))
(define parse-2 (make-parser #px"(1[0-9]|2[0-6])(.*)"))
```

That's what makes the ambiguity the most interesting. If only `0` were a valid digit... As it is, there are four possible cases (and these two functions handle them all!):


* `str` starts with 1 and a digit 0-9, parse both
* `str` starts with 2 and a digit 0-6, parse both
* `str` starts with 2 and a digit 7-9, parse 2 digits only
* `str` starts with 3-9, parse 1 digit only


And finally, try both:

```scheme
; Base case, so we can stop eventually
(if (equal? str "")
    '("")
    (append (parse-1 str) (parse-2 str)))
```

The base case looks a bit funny, since you might assume that if neither case matches we'll get there. That's the difference between the empty list `'()` and the list containing just an empty string `'("")`. In the latter, there's nothing to map against, ergo necessary.

And then all we need is the `n->char` function:

```scheme
; Convert a number 1-26 to a letter A-Z
(define (n->char n) (integer->char (+ 64 (string->number n))))
```

And that's it. Put it all together:

```scheme
; Given 1-26 mapping to A-Z, determine all possible words represented by a number
; Correctly resolve ambiguities where 1234 -> 1 2 3 4 = ABCD / 1 23 4 -> AWD / 12 3 4 -> LCD
(define (number->words str)
  ; Convert a number 1-26 to a letter A-Z
  (define (n->char n) (integer->char (+ 64 (string->number n))))

  ; Make an optional parser
  ; If the regex matches, add it to each possible next parse
  ; If it does not, return an empty list (to be appendable)
  (define (make-parser re)
    (λ (str)
      (match str
        [(regexp re (list _ n rest))
         (map (curry ~a (n->char n)) (number->words rest))]
        [any
         '()])))

  ; Create parsers for valid 1 digit and 2 digit letter numbers
  (define parse-1 (make-parser #px"([1-9])(.*)"))
  (define parse-2 (make-parser #px"(1[0-9]|2[0-6])(.*)"))

  ; Base case, so we can stop eventually
  (if (equal? str "")
      '("")
      (append (parse-1 str) (parse-2 str))))
```

Let's give it a try:

```scheme
> (number->words "1234")
'("ABCD" "AWD" "LCD")

> (number->words "8675309")
'("HFGECI")

> (length (number->words "85121215231518124"))

1181

> (number->words "85121215231518124")
'(... "HELLOWORLD" ...)
```

I could claim that I just happen to know the number code for `HELLOWORLD`, but really I wrote a quick inverse function:

```scheme
; Convert words back to numbers
(define (words->number str)
  (define (char->n c) (number->string (- (char->integer c) 64)))
  (apply ~a (for/list ([c (in-string str)]) (char->n c))))
```

Shiny!

Code: <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/number-words.rkt">number-words.rkt</a>

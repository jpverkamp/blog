---
title: The loneliest number...
date: 2012-08-17 20:08:13
programming/languages:
- Scheme
programming/sources:
- Lifehacker
---
I was reading the io9 article <a title="Why four is the nemesis of happy numbers" href="http://io9.com/5934819/why-four-is-the-nemesis-of-happy-numbers">Why four is the nemesis of happy numbers</a> and it got me thinking. Are there actually any cycles other than the one stated in the article? Why or why not?

<!--more-->

As a bit of background, the article is talking about "happy" numbers. Essentially, if you repeatedly sum the square of the digits in a number and eventually reach 1, you're a happy number. The example given in the article is 82:


| 82  |  8, 2   |  64 + 4 = 68  |
|-----|---------|---------------|
| 68  |  6, 8   | 36 + 64 = 100 |
| 100 | 1, 0, 0 | 1 + 0 + 0 = 1 |


So 82 is in fact happy. Any number that isn't happy is considered unhappy. Theoretically, the numbers have to either terminate at 1 or enter into a cycle, although at the moment, I don't have a proof for that. But it's actually even stranger than that. It turns out that (theoretically) all unhappy numbers eventually enter this cycle:

4, 16, 37, 58, 89, 145, 42, 20, 4

Why? Perhaps because eventually all numbers will be reduced to a single digit and 4 is the only one that loops.

But I was curious and I like writing scripts to test things like this. So I wrote up a bit of Scheme code (it runs just fine on <a title="(chez (chez scheme))" href="http://www.scheme.com/">Chez Scheme</a> and should work with only minimal modifications if any on other Schemes):

```scheme
; convert a number into a list of digits
(define (digits n)
  (if (zero? n)
      '()
      (cons (mod n 10) (digits (div n 10)))))

; square a number
(define (sqr n)
  (* n n))

; return either the terminal number (should be 1)
; or the point at which a cycle is detected
(define (happy n)
  (let ^ ([n n] [ns '()])
    (if (member n ns)
        n
        (^ (apply + (map sqr (digits n))) (cons n ns)))))

; go through all of the numbers, check if we have the cycle or 1
; print and exit if we find a counter example
(define (test)
  (let ([cycle '(1 4 16 37 58 89 145 42 20)])
    (let ^ ([i 1])
      (let ([res (happy i)])
        (when (not (member res cycle))
              (printf "~s\t~s\n" i res)
              (exit))
        (^ (add1 i))))))
```

Basically, it terminates whenever it sees a number that has already been calculated (so in the case of 1, it will repeat on 1 and stop; on any other loop it will eventually get back to the entry point).

I let the code crunch for a while and it's been running at an average of 1.66 kHz (1660 numbers per second). It's not perfect and I'm sure I could optimize it a bit with some [[wiki:memoization]](), but I've still checked the first 1.5 billion numbers. So far, everything is either happy or unhappy and goes through 4. I'll let it run for a while more and update this if it happens to find anything, but I doubt it.

Another interesting tidbit comes up with a <a href="http://io9.com/5934819/why-four-is-the-nemesis-of-happy-numbers?comment=51954505" title="io9 Comment">one of the comments</a>, showing that there are difference cycles in different bases. For example, hexadecimal has a loop around D:

D, A9, B5, 92, 55, 32, D

It turns out that at least bases 2 and 4 have no unhappy numbers (all sequences end in 1). Binary makes sense as it will always reduce down to one digit which would have to be 1 and 4 seems like it might be related to 4 looping in base 10. Maybe. And now I'm curious if there are any others. Another script to write if I have time.

If you'd like to download the source, you can do so here: <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/lonely-number.ss">lonely number source</a>
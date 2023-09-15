---
title: Taxicab numbers
date: 2012-11-10 14:00:00
programming/languages:
- Racket
- Scheme
programming/sources:
- Programming Praxis
---
Yesterday had another <a title="Taxicab Numbers" href="http://programmingpraxis.com/2012/11/09/taxicab-numbers/">programming puzzle</a> by Programming Praxis. This time, we are looking for a very special sort of number, a [[wiki:Taxicab number]]().  According to Wikipedia:


> In mathematics, the nth taxicab number, typically denoted Ta(n) or Taxicab(n), is defined as the smallest number that can be expressed as a sum of two positive algebraic cubes in n distinct ways.
> -- <cite>[[wiki:Taxicab number|Wikipedia: Taxicab Number]]()</cite>


<!--more-->

In this particularly problem, we're looking to verify that Ta(2) = 1729, that is that 1729 is the smallest number that can be written as the sum of two pairs of cubes. Given in the original question, we already know that 1729 can at least be written as the sum of two pairs of cubes as the cubes are given (1<sup>3</sup> + 12<sup>3</sup> and 9<sup>3</sup> + 10<sup>3</sup>). But can we prove that it's the smallest such number?

First, let's start with a helper function that can be used to find all of the cube pairs of a number. Basically, we can brute force the problem by trying all possible values for the first number, subtracting and taking the cube root for the second. If it's an integer, return it. 

Here's my first attempt:

```scheme
; list all pairs a, b such that a^3 + b^3 = n
(define (cube-pairs n)  
  (for/list ([i (in-range 1 n)]
             #:when (integer? (expt (- n (expt i 3)) 1/3)))
    (list i (expt (- n (expt i 3)) 1/3))))
```

And running it:

```scheme
> (cube-pairs 1729)
'((12 1))
```

Well, that's one pair. We were also expecting (9 10). So what happened? Well, let's look at the pieces of the `#:when`:

```scheme
> (expt 9 3)
729
> (- 1729 (expt 9 3))
1000
> (expt (- 1729 (expt 9 3)) 1/3)
9.999999999999998
```

All good until we get to the last line. There, we're having a bit of a problem. It seems that the floating point calculations mean that the cube root isn't actually an integer any more, even though it should be. So how do we fix that?

Well, my first idea is to calculate that same number as before and then round it to the nearest integer. We can then multiple the expression back out to test if it's actually a valid cube pair. Something like this:

```scheme
; list all pairs a, b such that a^3 + b^3 = n
(define (cube-pairs-2 n)  
  (define (j i) (inexact->exact (round (expt (- n (expt i 3)) 1/3))))
  (for/list ([i (in-range 1 (expt n 1/3))]
             #:when (let ([j (j i)])
                      (and (< i j)
                           (= (+ (* i i i) (* j j j)) n))))
    (list i (j i))))
```

And testing it again:

```scheme
> (cube-pairs2 1729)
'((1 12) (9 10))
```

Good to go. Granted, it's not exactly the best code, as we're recalculating the value of `(j i)`. I think that's a completely reasonable price to pay though, as we're only going to be doing the second calculation when we have a candidate answer. And that number is going to be dwarfed by the first comparison. So now something we have to worry about.

Moving on from there, the next step is to verify that Ta(2) = 1729 is actually true. For that to be the case, there cannot be a smaller number that has two cube pairs. So let's try that. Given n, find the first number that has n cube pairs:

```scheme
; find the taxicab number for n
; this is the number such that their exists a1...an and b1...bn such that
; a1^3 + b1^3 = ... = an^3 + bn^3 = some number
; for example, Ta(2) = 1729 = 1^3 + 12^3 = 9^3 + 10^3
(define (taxicab n)
  (let loop ([i 1])
    (if (= n (length (cube-pairs-3 i)))
        (list i (cube-pairs-3 i))
        (loop (+ i 1)))))
```

Simple, straightforward, and to the point. I love code like that. Let's just make sure it works all quicklike:

```scheme
> (taxicab 2)
'(1729 ((1 12) (9 10)))
```

And just for fun, let's check the next value:

```scheme
> (taxicab 3)
'(87539319 ((167 436) (228 423) (255 414)))
```

According to the answer on the [[wiki:Taxicab number|Wikipedia page]](), we're good to go. That took a while to run, so I don't think that I'll try any higher (apparently only the first six values are even known, with Ta(6) = 24,153,319,581,254,312,065,344 (26 sextillion). So who knows how large Ta(7) is... 

If you'd like to download today's code, you can do so here: <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/taxicab-numbers.rkt" title="GitHub: jpverkamp: Taxicab numbers">taxicab numbers source</a>
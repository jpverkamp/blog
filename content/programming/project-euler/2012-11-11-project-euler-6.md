---
title: Project Euler 6
date: 2012-11-11 14:00:14
programming/languages:
- Racket
- Scheme
programming/sources:
- Project Euler
---


> The sum of the squares of the first ten natural numbers is,

> 1<sup>2</sup> + 2<sup>2</sup> + ... + 10<sup>2</sup> = 385

> The square of the sum of the first ten natural numbers is,

> (1 + 2 + ... + 10)<sup>2</sup> = 55<sup>2</sup> = 3025

> Hence the difference between the sum of the squares of the first ten natural numbers and the square of the sum is 3025 - 385 = 2640.

> Find the difference between the sum of the squares of the first one hundred natural numbers and the square of the sum.
> -- <cite><a href="http://projecteuler.net/problem=6">PROJECT EULER #6</a></cite>

<!--more-->

This almost doesn't seem worth a post, being so straight forward, but I did say that I would work through all of the Project Euler problems. So of course I'll write it up. 

First, we need to write out a sum of squares and square of sums. We'll go ahead and make a function of each, designed to operate on a list. 

```scheme
; square a number
(define (sqr x) (* x x))

; sum the squares of a list
(define (sum-of-squares ls)
  (apply + (map sqr ls)))

; square the sum of a list
(define (square-of-sums ls)
  (sqr (apply + ls)))
```

And then just create the list and subtract the two:

```scheme
; diff between sum of squares and square of sums
(define (diff-of-sos n)
  (define ls (range 1 (+ n 1)))
  (- (square-of-sums ls)
     (sum-of-squares ls)))
```

Test it out with the given values in the problem:

```scheme
> (sum-of-squares (range 1 11))
385

> (square-of-sums (range 1 11))
3025

> (diff-of-sos 10)
2640
```

Good to go. Now we can scale up to the first 100:

```scheme
> (time (diff-of-sos 100))
cpu time: 0 real time: 0 gc time: 0
25164150
```

And there you have it. The difference between the two is already over 25 million and the code is lightning fast. 

Don't worry, problem 7 is a bit more interesting, getting back into prime numbers. And before long, the problems get really interesting indeed... 

As always, you can download my code for this or any Project Euler problem I’ve uploaded <a href="https://github.com/jpverkamp/small-projects/tree/master/project-euler" title="GitHub: jpverkamp: Project Euler">here</a>.
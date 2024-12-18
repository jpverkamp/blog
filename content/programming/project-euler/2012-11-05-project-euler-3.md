---
title: Project Euler 3
date: 2012-11-05 14:00:01
programming/sources:
- Project Euler
---


> The prime factors of 13195 are 5, 7, 13 and 29.

> What is the largest prime factor of the number 600851475143?
> -- <cite><a href="http://projecteuler.net/problem=3">PROJECT EULER #3</a></cite>

<!--more-->

This one is relatively straight forward and gives us the perfect opportunity to start working on prime numbers. They're absolutely fascinating, to the extend that I've posted about them a number of times before ([1]({{< ref "2012-10-22-prime-partitions-ii-the-listing.md" >}}), [2]({{< ref "2012-10-22-prime-partitions-ii-the-listing.md" >}}), [3]({{< ref "2012-11-01-the-sum-of-the-first-billion-primes.md" >}})).

To solve it, the first (and really only) thing that we need is a way to turn a number into a list of prime factors. How? It turns out that recursion makes this problem really pretty easy. 

Think of it this way: any number is either prime or can be written as the product of two numbers. If it can be written as the product of two numbers, then it has at least two prime factors (which may or may not be those numbers) and there must be a smallest prime factor. That number will be smaller than any other divisor of the number (otherwise it's either a smaller prime factor and would have been chosen as the smallest or it's a smaller composite and would contain a smaller prime factor that would have been chosen). 

All together, that means that if you start with 2 and loop upwards until you find a divisor, the first one you find is guaranteed to be the smallest prime factor of the given number. If you don't find one (and you can stop at the square root or you would have found the other multiple already), then the number itself is prime. 

Straight forward enough, yes?

```scheme
; test if n evenly divides m
(define (divides? m n)
  (= 0 (remainder m n)))

; find the prime factors of n
(define (prime-factors n)
  (define sqrtn (+ 1 (integer-sqrt n)))
  (let loop ([i 2])
    (cond
      [(> i sqrtn) (list n)]
      [(divides? n i) (cons i (prime-factors (/ n i)))]
      [else (loop (+ i 1))])))
```

The strength of it comes in at the line starting with `(divides? n i)`. Here, we know that we have the smallest prime factor of the current number, so we divide by that and recur. We know by recursion that `(prime-factors (/ n i))` will give us the rest of the prime factors and that they'll be greater than or equal to the first. 

Bam. That's it. Recursion is awesome!

A quick test to make sure that it's doing what it's supposed to:

```scheme
> (prime-factors 13195)
(5 7 13 29)
```

Everything looks good to go. So let's apply it to the actual problem at hand:

```scheme
; find the largest prime factor of a given number
(define (largest-prime-factor n)
  (apply max (prime-factors n)))
```

And test it out:

```scheme
> (time (largest-prime-factor 600851475143))
cpu time: 0 real time: 0 gc time: 0
6857
```

And there you have it. You could also work out this problem by hand, but it might take a while by trial division, as the full list of prime factors is `(71 839 1471 6859)`. Still, entirely doable.

As always, you can download my code for this or any Project Euler problem I’ve uploaded <a href="https://github.com/jpverkamp/small-projects/tree/master/project-euler" title="GitHub: jpverkamp: Project Euler">here</a>.
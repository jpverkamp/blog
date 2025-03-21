---
title: Project Euler 5
date: 2012-11-08 14:00:05
programming/languages:
- Racket
- Scheme
programming/sources:
- Project Euler
programming/topics:
- Mathematics
---


> 2520 is the smallest number that can be divided by each of the numbers from
> 1 to 10 without any remainder.

> What is the smallest positive number that is evenly divisible by all of the
> numbers from 1 to 20?
> -- <cite><a href="http://projecteuler.net/problem=5">PROJECT EULER #5</a></cite>

<!--more-->

Pretty straight forward today. Basically, we're looking for the [[wiki:least common multiple]]() (`lcm`) of all of the numbers from 1 to 20. So, we'll start with that. Here's a way to define `lcm`, directly from the wikipedia article:

{{< latex >}}lcm(a,b)=\frac{ |ab| }{gcd(a,b)}{{< /latex >}}

This translates pretty directly:

```scheme
; find the least common multiple of two numbers
; source: http://en.wikipedia.org/wiki/Least_common_multiple
(define (lcm a b)
  (/ (abs (* a b)) (gcd a b)))
```

Luckily, `lcm` is commutative, so `(lcm (lcm a b) c)` is the same as `(lcm a (lcm b c))`, etc.

However, as you may have noticed, we need another function: `gcd` (the [[wiki:greatest common divisor]]()). Euclid's algorithm is both straight forward and nicely expressed in a recursive fashion:

{{< latex >}}gcd(a,b) = \begin{cases} a &amp;\mbox{if } b=0 \\ gcd(b,mod(a,b)) &amp; \mbox{otherwise} \end{cases}{{< /latex >}}

And now in code:

```scheme
; find the greatest common divisor of two numbers
; source: http://en.wikipedia.org/wiki/Greatest_common_divisor
(define (gcd a b)
  (if (= b 0)
      a
      (gcd b (remainder a b))))
```

With that, it's nice and easy to calculate the least common multiple of 1 through any number n. Just use the same `for/fold` macro I talked about [yesterday ]({{< ref "2012-11-07-project-euler-4.md" >}})(albeit without the `*`):

```scheme
; calculate the least common multiple of a range
(define (least-common-multiple-up-to n)
  (for/fold ([res 1])
            ([i (in-range 1 (+ n 1))])
    (lcm res i)))
```

So we start with the result `res` at 1 then repeatedly take the `lcm` of the current result and the new number. Check it on the small example given:

```scheme
> (time (least-common-multiple-up-to 10))
cpu time: 0 real time: 0 gc time: 0
2520
```

Good to go. Extend it for the full example:

```scheme
> (time (least-common-multiple-up-to 20))
cpu time: 0 real time: 0 gc time: 0
232792560
```

And we're good to go. You can't really beat 0 ms.

As always, you can download my code for this or any Project Euler problem I’ve uploaded <a href="https://github.com/jpverkamp/small-projects/tree/master/project-euler" title="GitHub: jpverkamp: Project Euler">here</a>.
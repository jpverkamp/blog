---
title: Project Euler 1
date: 2012-11-03 14:00:28
programming/languages:
- Racket
- Scheme
programming/sources:
- Project Euler
programming/topics:
- Mathematics
---



> If we list all the natural numbers below 10 that are multiples of 3 or 5,
> we get 3, 5, 6 and 9. The sum of these multiples is 23.

> Find the sum of all the multiples of 3 or 5 below 1000.
> -- <cite><a href="http://projecteuler.net/problem=1">Project Euler #1</a></cite>


<!--more-->

We start off relatively simple, just asked to sum up a thousand numbers. `for/sum` does exactly what we want, looking over all of the values and adding them up. The `#:when` clause does the rest, limiting it to just numbers divisible by 3 or 5. 

```scheme
(define (sum-divisibles limit)
  (for/sum ([i (in-range 1 limit)]
            #:when (or (divides? i 3)
                       (divides? i 5)))
    i))

; test if n evenly divides m
(define (divides? m n)
  (= 0 (remainder m n)))
```

```scheme
> (time (sum-divisibles 1000))
cpu time: 0 real time: 1 gc time: 0
233168
```

Alternatively, this could be done using a bit of discrete mathematics. We have three arithmetic series of interest:

The sum of numbers divisible by 3:

{{< latex >}}div_3 = 3 + 6 + ... + 999 = (\frac{999}{3})(\frac{3 + 999}{2}) = 166833{{< /latex >}}

The sum of numbers divisible by 5:

{{< latex >}}div_5 = 5 + 10 + ... + 995 = (\frac{995}{5})(\frac{5 + 995}{2}) = 99500{{< /latex >}}

The sum of numbers divisible by 3 and 5. Since `lcm(3,5) = 15`, this is equivalent to the sum of numbers divisible by 15:

{{< latex >}}div_15 = 15 + 30 + ... + 990 = (\frac{990}{15})(\frac{15 + 990}{2}) = 33165{{< /latex >}}

All together, we need to add the numbers divisible by 3 and 5. Since the numbers divisible by 15 are counted in both, subtract one copy of those:

{{< latex >}}div_3 + div_5 - div_15 = 166833 + 99500 - 33165 = 233168{{< /latex >}}

And there you have it. The first of (hopefully) many posts on Project Euler.

If you'd like to download my code for this or any Project Euler problem I've uploaded it <a href="https://github.com/jpverkamp/small-projects/tree/master/project-euler" title="GitHub: jpverkamp: Project Euler">here</a>.
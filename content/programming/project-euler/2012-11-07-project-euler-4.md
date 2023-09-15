---
title: Project Euler 4
date: 2012-11-07 14:00:48
programming/languages:
- Racket
- Scheme
programming/sources:
- Project Euler
programming/topics:
- Mathematics
---


> A palindromic number reads the same both ways. The largest palindrome made from the product of two 2-digit numbers is 9009 = 91 x 99.

> Find the largest palindrome made from the product of two 3-digit numbers.
> -- <cite><a href="http://projecteuler.net/problem=4">PROJECT EULER #4</a></cite>

<!--more-->

The idea behind solving this problem in the brute force is relatively straight forward, just multiple every pair of three digit numbers, recording the best product (that is also a palindrome) as you go.

First, we need a way to split a number into it's digits. It turns out that this will be useful for several of the problems that we'll have to do on Project Euler, so at some point, I'm going to want to extract this out into a shared library (along with many of the prime functions I've already used). The idea is simple though. If you have any number, the list of digits in the number is equivalent to the last digit (the remainder of the number divided by 10) concatenated with the rest of the digits (integer division by 10). Then at the end, you can reverse the list and you're good:

```scheme
; return a list of the digits of n
(define (digits n)
  (reverse
   (let loop ([n n])
     (cond
       [(< n 10) (list n)]
       [else
        (cons (remainder n 10)
              (loop (quotient n 10)))]))))
```

Optimally though, we'd like to be able to do that without the `reverse`. In all of the cases that we're working on here, we're only reversing the elements of a four element list, so the run-time is negligible, but if we're hoping to put it in a library than it we should at least look into some minor optimizations.

The answer in this case, is to make the function [[wiki:tail recursive]](). What that means in theory is that you never have any work waiting for you when you return from a function call so you can actually skip through several stack frames all at the same time (or never store them in the first place). Scheme and by extension Racket guarantees that tail calls will optimized, which is actually one of the reasons that recursive code in Schemes works just as well (and in many cases compile to nearly identical code) as loops in iterative languages such as C or Java.

What that means in practice though, is that if you have a problem where you need to use `reverse` to get the answer that you were expecting, in all likelihood, you want to use tail recursive (if you weren't already) or remove the tail recursive you have (if you were). Instead, you'll often find that keeping an accumulator list that you can build up as you're going is more helpful. In this case:

```scheme
; return a list of the digits of n
(define (digits n)
  (let loop ([n n] [ls '()])
    (cond
      [(< n 10) (cons n ls)]
      [else (loop (quotient n 10)
                  (cons (remainder n 10) ls))])))
```

So instead of using returning from a function to build up the resulting list, we build it in a parameter to `loop`, returning it directly at the end. The result is exactly the same, although with crazy huge numbers there should be a performance boost. It's primarily from making use of the tail call optimization, but there's also a bit from not needing to use `reverse`.

Back to the original problem though, the next step is to determine when a number is a palindrome. Since we can already generate lists of numbers, that becomes the problem of if we can determine if a list is a palindrome. And what is a palindrome, other than something that reads that same forwards and backwards? Well, that's exactly what we need to solve this problem.

```scheme
; test if a number is a palindrome
(define (palindrome? n)
  (equal? (digits n)
          (reverse (digits n))))
```

With that, we can actually approach the problem that we started with. We'll start with the direct solution that I mentioned earlier, just trying all possible combinations and remembering the largest one:

```scheme
; find the largest product of n digit numbers that's a palindrome
(define (largest-palindrome-product digits)
  (define lo (expt 10 (- digits 1)))
  (define hi (expt 10 digits))
  (for*/fold ([best 0])
             ([x (in-range lo hi)]
              [y (in-range x hi)]
              #:when (palindrome? (* x y)))
    (max best (* x y))))
```

The strength of this solution comes from the `for*/fold` macro which is similar to the other `for` macros we've used previously, except this time there are two sets of parameters. In addition to the normal looping parameters (`x` and `y`), there's a new variable `best`. What this does is to basically work as an accumulator, like we were working with earlier. For each iteration of the function, whatever the body returns becomes the new value of `best`. So in this case, we're going to find the maximum product.

Another intricacy that I may not have previously mentioned is the `*` in `for*/fold`. What that means is that we're actually creating nested `for` loops, similar to how `let*` turns into nested calls to `let`. So the code above is actually equivalent to something more like this:

```scheme
(for/fold ([best 0])
          ([x (in-range lo hi)])
  (max best
       (for/fold ([inner-best 0])
                 ([y (in-range x hi)]
                  #:when (palindrome? (* x y)))
         (max inner-best (* x y)))))
```

*Note: I'm not actually sure that's what Racket would produce, but at least this would be equivalent code if `for*/fold` were not available.*

In any case, either version should do what we want, so let's try it out:

```scheme
> (time (largest-palindrome-product 3))
cpu time: 1154 real time: 1145 gc time: 188
906609
```

And there you have it. The largest palindrome product of two three digit numbers is 906,609. A second is still pretty slow, but we can boost that slightly, as there's another solution that I want to look into. Think of this. We are trying to generate a palindrome `abccba` (where any of those numbers might be repeats). That could alternatively be written as:

```
`100000a + 10000b + 1000c + 100c + 10b + a
= 100001a + 10010b + 1100c
= 11(9091a + 910b + 100c)`
```

Since 11 is prime, this tells us that at least one of the numbers must be divisible by 11. So we can revise the earlier code to only use multiples of 11 for the first number (although we lose the general solution):

```scheme
; find the largest product of 3-digit numbers that's a palindrome
(define (faster-largest-palindrome-product)
  (for*/fold ([best 0])
             ([x (in-range 11 1000 11)]
              [y (in-range x 1000)]
              #:when (palindrome? (* x y)))
    (max best (* x y))))
```

And run it:

```scheme
> (time (faster-largest-palindrome-product))
cpu time: 156 real time: 156 gc time: 62
906609
```

That got us about an order of magnitude (which makes sense as we're jumping by an order of magnitude more), but let's see if we can't do better yet. 

Consider the product we're working with, `(100a + 10b + c)(100d + 10e + f)`, which expands to:

```
`                   100cd + 10ce + cf +
          1000bd + 100be + 10bf +
10000ad + 1000ae + 100af
`
```

If we start with the assumption that the first digit of the number is 9 (we can go back and change this later if it doesn't work out), then the last digit is also 9, so `cf = 9`. The only possible pairs of digits that multiply to 9 are `1/9`, `3/3`, and `7/7`. That at least gives us that both numbers are going to be odd, so we'll make that assumption:

```scheme
; find the largest product of 3-digit numbers that's a palindrome
(define (fastest-largest-palindrome-product)
  (for*/fold ([best 0])
             ([x (in-range 11 1000 22)]
              [y (in-range x 1000 2)]
              #:when (palindrome? (* x y)))
    (max best (* x y))))
```

This should buy us about another 4x speedup as we're cutting out even numbers on each of the two loops. 

```scheme
> (time (fastest-largest-palindrome-product))
cpu time: 32 real time: 26 gc time: 0
906609
```

And there you have it. With some simple linear algebra (barely even deserving of the name), we cut the runtime from 1154 ms down to 32 ms, for a speedup of approximately 35x. That's none too shabby at all. It's always something to keep in the back of your mind. 

Although on the flip side, in real life, it's don't get carried away with [[wiki:Premature optimization#When to optimize|premature optimization]](). As Donald Knuth once said, *premature optimization is the root of all evil*. :smile:

As always, you can download my code for this or any Project Euler problem I’ve uploaded <a href="https://github.com/jpverkamp/small-projects/tree/master/project-euler" title="GitHub: jpverkamp: Project Euler">here</a>.

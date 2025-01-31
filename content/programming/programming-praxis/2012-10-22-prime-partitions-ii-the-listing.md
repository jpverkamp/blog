---
title: 'Prime Partitions II: The Listing'
date: 2012-10-22 14:00:58
programming/languages:
- Racket
- Scheme
programming/sources:
- Programming Praxis
programming/topics:
- Mathematics
- Prime Numbers
---
As the continuation of [Saturday's post]({{< ref "2012-10-22-prime-partitions-ii-the-listing.md" >}}) on counting the number of prime partitions of a number without actually determining what those partitions are, today we're going to work out the actual list of partitions.

<!--more-->

To start with, we're going to need some way of generating a list of primes. Using a `generator`, the code is rather straight forward. Start with 2 and 3. After that, loop through the odd numbers, checking if each in turn is prime. For the ones that are, `yield` them. Something like this:

```scheme
(require racket/generator)

; create a generator of primes between min and max (inclusive)
; if max is #f, return an infinite generator
(define (primes [min 2] [max #f])
  (generator ()
    (when (>= 2 min)
      (yield 2))
    (let loop ([i 3])
      (when (or (not max) (<= i max))
        (when (and (>= i min) (prime? i))
          (yield i))
        (loop (+ i 2))))
    (yield #f)))
```

There's one additional part to this code--the optional parameters `min` and `max` that control just which primes you want. Basically, return a `generator` that will generate all of the primes between `min` and `max` inclusive. So we have:

```scheme
> (for/list ([i (in-producer (primes 20 40) #f)]) i)
'(23 29 31 37)
```

The `in-producer` will take any function (like the one created by `primes`) and call it over and over again until a given value--`#f` in this case--is returned. 

To make this work though, you need a way to determine if a number is prime, so that's the second part of today's post. To determine if a number is prime, we basically use the exact same code as the [previous post]({{< ref "2012-10-22-prime-partitions-ii-the-listing.md" >}}), except we return `#t` or `#f` instead of the factors:

```scheme
; is n prime?
(define (prime? n)
  (define rootn (sqrt n))
  (cond
    [(= n 1) #f]
    [(divides? n 2) #f]
    [else
     (let loop ([i 3])
       (cond
          [(> i rootn) #t]
          [(divides? n i) #f]
          [else
           (loop (+ i 2))]))]))
```

Now with these two pieces in place, all we have to do is write a function to generate the actual partitions. The idea is straightforward. Go through all primes lower than the given number. For each, recur on the original number minus the prime, noting that we only want further primes to be greater or equal. That way the lists will be naturally sorted. If we ever get exactly 0, there's one way to add numbers to get it--add none of them. If we go below 0, there's no hope any more. So how does that all translate into code?

```scheme
; calculate the prime partitions of n
; min is the smallest prime to consider for the recursion
(define (prime-partitions n [min 2])
  (cond
    [(< n 0) '()]
    [(= n 0) '(())]
    [else
     (for*/list ([i (in-producer (primes min n) #f)]
                 [r (prime-partitions (- n i) i)])
       (cons i r))]))
```

The nice thing about this is that it will nest the loops over primes `i` and recursive results `r` using that prime. With this, any branches that don't actually produce a result just don't appear. I have a feeling that some of my older code could better be written in this same style.

A few examples:

```scheme
> (prime-partitions 5)
'((2 3) (5))
> (prime-partitions 11)
'((2 2 2 2 3) (2 2 2 5) (2 2 7) (2 3 3 3) (3 3 5) (11))
> (prime-partitions 15)
'((2 2 2 2 2 2 3)
  (2 2 2 2 2 5)
  (2 2 2 2 7)
  (2 2 2 3 3 3)
  (2 2 3 3 5)
  (2 2 11)
  (2 3 3 7)
  (2 3 5 5)
  (2 13)
  (3 3 3 3 3)
  (3 5 7)
  (5 5 5))
```

And that's all there is to it. I think perhaps I won't be calling `(prime-partitions 1000)` though. :smile:

If you'd like to download the source for this post, you can do so here: <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/get-prime-partitions.rkt" title="get-prime-partitions source">get-prime-partitions source</a>

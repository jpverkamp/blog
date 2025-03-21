---
title: One Billion Primes - Segmented Sieve
date: 2012-11-29 22:00:31
programming/languages:
- Racket
- Scheme
programming/sources:
- Programming Praxis
programming/topics:
- Mathematics
- Prime Numbers
---
After a [sum of the first billion primes]({{< ref "2012-11-01-the-sum-of-the-first-billion-primes.md" >}}) post (originally from <a title="Programming Praxis: The Sum Of The First Billion Primes" href="http://programmingpraxis.com/2012/09/11/the-sum-of-the-first-billion-primes/">Programming Praxis</a>), I decided to finally write a segmented version of the [[wiki:Sieve of Eratosthenes|Sieve of Eratosthenes]]().

<!--more-->

Basically, the idea is not to make a sieve for the entire 23 billion numbers that you'll be summing, instead just make a sieve for the first square root of them. This is guaranteed to contain all of the primes you will need to divide by for the rest of the list. After that, just reuse that same vector over and over again until you've counted enough primes. This should definitely help with the memory issues I was having and should also be much faster (we can take better advantage of memory caches).

If you'd like to follow along, the entire code is available on <a title="GitHub: Segmented billion primes source" href="https://github.com/jpverkamp/small-projects/blob/master/blog/billion-primes-segmented.rkt">GitHub</a>.

First we need to create the initial sieve. This code is nearly identical to the original sieve code except we're only sieving up to the square root of the upper bound on the nth prime.

```scheme
; sieve up to sqrt of the estimated high prime
(define-values (lo hi) (guess-nth-prime n))
(define sieve-size (+ 1 (integer-sqrt hi)))
(define sieve (make-vector sieve-size #t))
(vector-set! sieve 0 #f)
(vector-set! sieve 1 #f)
(for* ([i (in-range 2 sieve-size)]
       #:when (vector-ref sieve i)
       [j (in-range (* i i) sieve-size i)])
  (vector-set! sieve j #f))
```

And then we can turn that directly into a list of primes:

```scheme
; create a list of just those primes
(define primes
  (for/list ([i (in-naturals)]
             [p? (in-vector sieve)]
             #:when p?)
    i))
(define sum (apply + primes))
(define cnt (length primes))
```

The next step starts the loop that will segment and sum the primes. First, code:

```scheme
; reuse the sieve in blocks until we've found enough
  (let loop ([lo sieve-size])
    ; clear the vector
    (for ([i (in-range sieve-size)]) (vector-set! sieve i #t))

    ; remove all multiples of candidate primes
    (for* ([p (in-list primes)]
           [i (in-range (if (divides? lo p) 0 (- p (mod lo p))) sieve-size p)])
      (vector-set! sieve i #f))

    ; add new primes to sum and count
    (for ([i (in-range lo (+ lo sieve-size))]
          [p? (in-vector sieve)]
          #:when (and p? (< cnt n)))
      (set! sum (+ sum i))
      (set! cnt (+ cnt 1)))

    ; if we're done, return the result, otherwise loop
    (if (= cnt n)
        sum
        (loop (+ lo sieve-size)))))
```

As mentioned, we have to start by clearing out the previous values. After that, we want to remove candidates. This is a bit tricky as this segment doesn't necessarily (actually doesn't often) start at a multiple of each prime, so you have to find the first one. That's what the `(if (divides? lo p) 0 (- p (mod lo p)))` bit does.

Then, you simply go through this segment and add all of the primes into our running total. There's a bit of inefficiency here as we loop through the rest of the segment even when we hit our count, but I think that's actually acceptable. The next version of Racket will have a `#:break` parameter in `for` which would help in this case, but as it is, we're not losing much.

And there you have it. This should be everything we need to sum primes with a segmented sieve. Let's try it out:

```scheme
> (for ([n (in-list '(10000 20000 30000))])
    (printf "~s:\n" n)
    (printf "~s\n\n" (time (sum-primes n))))

10000:
cpu time: 7 real time: 8 gc time: 0
496165411

1000000:
cpu time: 897 real time: 894 gc time: 0
7472966967499

1000000000:
cpu time: 1512636 real time: 1510899 gc time: 3836
11138479445180240497
```

Yes, you read that right. It only took a bit under half an hour (25 minutes 12 seconds) to sum the first billion primes where previously it had taken 2 hours 42 minutes for the Sieve of Eratosthenes and 1 hour 28 minutes for the Sieve of Atkin. It turns out that paying a bit of attention to memory access isn't necessarily a bad thing. :smile:

If you'd like to check out / download the entire code, you can do so here:
- <a title="GitHub: Segmented billion primes source" href="https://github.com/jpverkamp/small-projects/blob/master/blog/billion-primes-segmented.rkt">segmented version</a>
- <a title="GitHub billion primes source" href="https://github.com/jpverkamp/small-projects/blob/master/blog/billion-primes.rkt">original version</a>

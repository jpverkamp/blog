---
title: Nested Primes
date: 2012-12-22 14:00:17
programming/languages:
- Racket
- Scheme
programming/sources:
- Programming Praxis
programming/topics:
- Prime Numbers
---
<a href="http://programmingpraxis.com/2012/12/21/building-primes/" title="Building Primes">Yesterday's post</a> from Programming Praxis poses an interesting problem: find the largest prime *n* such that the result of repeatedly removing each digit of *n* from left to right is also always prime.

For example, 6317 would be such a number, as not only is it prime, but so are 317, 17, and 7.

<!--more-->

This is actually a surprisingly straightforward problem, if instead of starting at the largest such number and checking to make sure that each part along the way is prime, you start with the single digit primes (2, 3, 5, and 7) and repeatedly add on numbers to the left so long as they are prime.

For example, 3 would become 13, 23, 43, 53, 73, and 83. 13 in turn would become 113, 313, and 613. It turns out though that this list doesn't grow unbounded. Eventually each branch will terminate (a proof for why this happens would be interesting, but I'm not sure how it would work--or even if such a thing is provable short of proof by enumerating all of the solutions).

Enough on discussion though, it's code time!

(Only Racket today as I'm running a bit short on time for my writeup. If anyone would like a Python version as well, let me know in the comments and I'll write one up.)

```scheme
; find the largest prime such that each number produced by
; removing digits from the left side is still prime
; #:root - the prime to start at, 0 for all primes
; #:limit - the largest prime to check
(define (largest-nested-prime
         #:root [root 0]
         #:limit [limit +inf.0])
  ; loop starting at the root
  (let loop ([n root])
    (cond
      ; if we're over the limit, no largest prime
      [(> n limit) 0]
      ; otherwise, try each prefixed digit while still prime
      [else
       (define multiplier (expt 10 (digits n)))
       ; use for/fold to emulate what for/max would do
       (for/fold ([best n])
                 ([i (in-range 1 10)]
                  #:when (prime? (+ (* multiplier i) n)))
         ; return the best of the current and the nested
         (max best (loop (+ (* multiplier i) n))))])))
```

That's a whopping 10 lines of code if you remove the comments and collapse the define back into a single line. Not too bad for what it's calculating.

It takes rather a while to run, but eventually you'll get an answer:

```scheme
> (largest-nested-prime)
357686312646216567629137
```

What I'm curious about though, is there a better way to do this? I used the trial division method of determining if a number was prime, but I wonder if either a statistical method or perhaps a sieve would work better. Perhaps it'll be something to try one day if I get bored. :smile:

One additional thing I did was to work out the nested tree structure that you get with something like this. The code is available at <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/nested-primes.rkt" title="GitHub: Nested primes source">GitHub</a>, but here's a sample run just to whet your appetite:

```scheme
> (nested-primes #:root 3 #:limit 1000)
'(3
  (13 (113) (313) (613))
  (23 (223) (523) (823))
  (43 (443) (643) (743))
  (53 (353) (653) (853) (953))
  (73 (173) (373) (673) (773))
  (83 (283) (383) (683) (883) (983)))
```

Here's a nice chart of that:

{{< figure src="/embeds/2012/3-nested-primes.png" >}}

My goal is to generate a list of all such primes and make a graph of them all, just to see if there's any sort of visual pattern. I was going to include that in this post, but I have a feeling that code is going to take more than a little time to generate (and actually returning the list directly isn't probably a good idea as that way it all has to exist in memory at the same time). So I'll probably optimize this and post it again later. Graph visualization is fun!

If you'd like to download the full code for today's post, you can do so here: <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/nested-primes.rkt" title="GitHub: Nested primes source">nested primes source</a>

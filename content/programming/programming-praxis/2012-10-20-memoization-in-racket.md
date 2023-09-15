---
title: Memoization in Racket
date: 2012-10-20 13:55:48
programming/languages:
- Racket
- Scheme
programming/sources:
- Programming Praxis
programming/topics:
- Data Structures
---
[[wiki:Memoization]]() is awesome! 

I've already written [one post]({{< ref "2012-09-29-pickles-and-memoization.md" >}}) on the subject in Python, but this time we'll do the same in Racket. It's particularly timely as without it, [today's post]({{< ref "2012-10-22-prime-partitions-ii-the-listing.md" >}}) on determining the number of prime partitions of a number would take longer to run than I care to wait.

<!--more-->

The basic macro isn't actually too bad. Basically, we want to create a function with an associated hash table associating arguments with their result. It doesn't work out so well if the function is non-deterministic or has state of its own, but for a purely functional solution, it's exactly what we're looking for. 

```scheme
; replace define with a memoized version
(define-syntax define-memoized
  (syntax-rules ()
    [(_ (f args ...) bodies ...)
     (define f
       ; store the cache as a hash of args => result
       (let ([results (make-hash)])
         ; need to do this to capture both the names and the values
         (lambda (args ...)
           ((lambda vals
              ; if we haven't calculated it before, do so now
              (when (not (hash-has-key? results vals))
                (hash-set! results vals (begin bodies ...)))
              ; return the cached result
              (hash-ref results vals))
            args ...))))]))
```

The code gets a bit strange on the inner part as I'm actually creating two functions only to immediately apply the inner one. Why? Because it's the only way that I could think of to capture both the names of the arguments and their values (which are the actual key to the hash). If you have a better solution, I'd love to hear it. :smile:

But with that, it's really straight forward to turn a normal function into a memoized one. Here's an example using that particularly poor way of writing Fibonacci: 

```scheme
; example, fibonacci without memoization
(define (fib n)
  (cond
    [(< n 1) 1]
    [else (+ (fib (- n 1)) (fib (- n 2)))]))

; example, fibonacci with memoization
(define-memoized (mfib n)
  (cond
    [(< n 1) 1]
    [else (+ (mfib (- n 1)) (mfib (- n 2)))]))
```

So, moment of truth. Does it work?

```scheme
> (time (fib 35))
cpu time: 5022 real time: 5038 gc time: 37
24157817

> (time (mfib 35))
cpu time: 0 real time: 0 gc time: 0
24157817
```

I'd say that's a pretty definitive yes. With this, we can calculate values we wouldn't even have considered with the non-memoized version. 

```scheme
> (time (mfib 1000))
cpu time: 2 real time: 1 gc time: 0
113796925398360272257523782552224175572745930353730513145086634176691092536145
985470146129334641866902783673042322088625863396052888690096969577173696370562
180400527049497109023054114771394568040040412172632376
```

And that's all there is too it. Memoization in Racket. Bam!

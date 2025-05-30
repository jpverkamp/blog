---
title: User space continuation-based thread pool
date: 2013-04-23 21:00:14
programming/languages:
- Racket
programming/topics:
- Concurrency
- Continuations
---
I'm perhaps a little late to last week's <a title="Reddit: DailyProgrammer" href="http://www.reddit.com/r/dailyprogrammer/">DailyProgrammer</a> challenge to <a title="[04/01/13] Challenge #122 [Intermediate] User-Space Threading" href="http://www.reddit.com/r/dailyprogrammer/comments/1ceai7/040113_challenge_122_intermediate_userspace/">implement a user-space threading system</a>, without using any sort of built in thread library, but it just sounded too interesting to pass up.

<!--more-->

The full challenge states that we are to:

> Your goal is to implement an *efficient* and *dynamic* user-level threading library. You may implement this in any language and on any platform, but you may not use any existing threading code or implementation, such as the Win32 threading code or the UNIX pthreads lib. You may call system functions (such as interrupts and signals), but again cannot defer any thread-specific work to the operating system.

The only two solutions posted thus far use <a title="JavaScript solution" href="http://www.reddit.com/r/dailyprogrammer/comments/1ceai7/040113_challenge_122_intermediate_userspace/c9foc4n">JavaScript's setTimeout method</a> (which arguably is already thread specific functionality) or <a title="Haskell solution" href="http://www.reddit.com/r/dailyprogrammer/comments/1ceai7/040113_challenge_122_intermediate_userspace/c9g27et">Haskell and the 'free' monad</a>[^1]. For a bit of variety, I'll be using [[wiki:continuations]](), essentially to implement [[wiki:coroutines]]() with manual scheduling.

Before we get started, if you'd like to follow along, you can do so here:
- <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/continuation-thread-pool.rkt">continuation thread pool on GitHub</a>

That being said, essentially, we need two methods:

* `(threads thunk ...)` - takes a series of thunks and runs them in parallel
* `(yield)` - within a thread, turns over control to the next thread in the pool

Even before that, we're going to want a bit of structure. First, we'll wrap the thread data up in a structure:

```scheme
; Store the current state of a thread
(define-struct thread-state (continuation) #:mutable)
```

All that we're going to save is a continuation. If you haven't looked into continuations, the essential idea is that it's a function that wraps up 'everything that you need to do next' if you were to suspend the current execution of the function. For example (using `call/cc` as the alias for `call-with-current-continuation` to capture the continuation):

```scheme
> (+ 1 (call/cc (lambda (k) (+ 2 (k 3)))))
4
```

Why this works is that `call/cc` captures `(+ 1 ...)` as a function. We then later apply that function to 3 for the result of 4, completely ignoring the `(+ 2 ...)` part. If that makes sense, great! If not... well, perhaps you should read up a bit more on continuations... They're an amazingly powerful construct that allows for some remarkably powerful control flow structures. In this case, just know that we can always treat them as a function which can suspend control and later to call it with what we want it to return.

So essentially, we're going to set up each `thread-state` with a psuedo-continuation. But we'll get to that in a second. We still haven't set up the data structure for the `thread-pool`:

```scheme
; Store a collection of threads in a pool
(define-struct thread-pool (all current switch-count) #:mutable)

; Create a new, empty thread pool
(define (make-empty-thread-pool)
  (make-thread-pool '() '() 0))

; Allow for multiple thread pools
(define current-thread-pool 
  (make-parameter (make-empty-thread-pool)))

; Get the number of context switches out of the current thread pool
(define (get-switch-count [pool (current-thread-pool)])
  (thread-pool-switch-count pool))
```

The `switch-count` isn't strictly necessary, but it will allow us to do some amount of performance evaluation when all is said and done. Other than that, `all` will hold a list of all of the threads that we're dealing with while `current` is that same list only advanced to the currently executing thread. So we're not doing anything fancy with thread priorities, although we could easily do so by replacing `current` with a [[wiki:priority queue]]() rather than a simple list[^2]. 

So how do we do all of that? Well, here is `threads` to create the initial state:

```scheme
; Run a given list of thunks in parallel
(define (threads . thunks)
  (call-with-current-continuation
   (lambda (k)
     (when (null? thunks) (error 'threads "must specify at least one thread"))

     ; Unwrap the current pool
     (define pool (current-thread-pool))

     ; Create the initial thread states
     (define threads
       (map 
        (lambda (thunk) (thread-state (lambda (_) (k (thunk)))))
        thunks))

     ; Store them in the pool
     (set-thread-pool-current! pool (append (thread-pool-current pool) threads))
     (set-thread-pool-all! pool (append (thread-pool-all pool) threads))

     ; Start the first thread
     (define first-k (thread-state-continuation (car (thread-pool-current pool))))
     (first-k (void)))))
```

So basically, we get a thread pool (I'll show you some of the advantages of doing it this way later), create the threads, store them in the thread pool structure, and start the first thread. Everything should be good to go. 

(There's also a sneaky part there where we capture the continuation immediately and us it in each thread. I'll get to that too later.)

But for everything to work, we also need `yield`:

```scheme
; Yield control of the current thread to the next thread in the current pool
(define (yield)
  (call-with-current-continuation
   (lambda (k)
     ; Unwrap the current pool
     (define pool (current-thread-pool))

     ; Store the current thread state
     (define thread (car (thread-pool-current pool)))
     (set-thread-state-continuation! thread k)

     ; Advance to the next thread
     (set-thread-pool-current! pool (cdr (thread-pool-current pool)))
     (when (null? (thread-pool-current pool))
       (set-thread-pool-current! pool (thread-pool-all pool)))
     (set-thread-pool-switch-count! pool (+ 1 (thread-pool-switch-count pool)))

     ; Run that thread
     (define next-k (thread-state-continuation (car (thread-pool-current pool))))
     (next-k (void)))))
```

When it is first called, this will capture the continuation for the current thread. The first step that it will do when unwrapping is return from the `yield` itself, but after that it will hand control back to the other, previous continuations. This is then stored in the first (running) thread's `thread-state` and then the `thread-pool` is advanced to the next `thread`, which is then run just as the first was started in `threads`.

So how can we use something like that? Well, let's implement the fairly standard 'tick tock' test for threads:

```scheme
(define (tick-tock-test)
  (parameterize ([current-thread-pool (make-empty-thread-pool)])
    (threads 
     ; Keep printing tick
     (lambda ()
       (let loop ()
         (printf "tick\n")
         (yield)
         (loop)))
     ; Keep printing tock
     (lambda ()
       (let loop ()
         (printf "tock\n")
         (yield)
         (loop))))))
```

Run it[^3] and you should see something like this:

```scheme
> (tick-tock-test)
tick
tock
tick
tock
tick
tock
...
```

Exactly what we were looking for. But the real strength comes in when you try to do some more interesting examples. For example, let's calculate Fibonacci values in parallel. Remember when I mentioned capturing a continuation in `threads`? This is when it comes in handy:

```scheme
(define (fibonacci-test)
  (define (fib n)
      (yield)
      (if (<= n 1)
          1
          (+ (fib (- n 1)) (fib (- n 2)))))

  (parameterize ([current-thread-pool (make-empty-thread-pool)])
    (threads
     (lambda () (list 20 (fib 20)))
     (lambda () (list 10 (fib 10))))))
```

Take a moment and guess what you think that should do. 

In traditional threads, it wouldn't do anything, since threads don't generally return anything. But in this case, the threads have a continuation that will return from `threads` (the initial one we captured). So whichever thread returns first (and finally gets back to that original continuation) will return a value. So if we test it:

```scheme
> (fibonacci-test)
'(10 89)
```

So essentially, we've implemented the `amb` operator first described back in a variation on McCarthy’s amb operator for ambiguous choice[^4]. It may not be exactly what you're looking for in a threading system, but if that's the case, you can always use a different one. :smile: More seriously, if you don't want the `thread-pool` to exit when the first thread has a value, just don't return.

As our next test, let's figure out just how efficient it is[^5]. So we'll use the `switch-count` functionality we built in earlier:

```scheme
(define (timing-test)
  (define iterations 1000000)

  (parameterize ([current-thread-pool (make-empty-thread-pool)])
    (time
     (threads
      (lambda () 
        (let loop ([i 0])
          (when (< i iterations)
            (yield)
            (loop (+ i 1)))))))
    (printf "~a context switches (target: ~a)\n" 
            (get-switch-count)
            iterations)))
```

So how long does it take to do 1 million switches?

```scheme
> (timing-test)
cpu time: 9479 real time: 10969 gc time: 2489
1000000 context switches (target: 1000000)
```

Honestly, that's pretty terrible for a threading system. That works out to ~10 ms per context switch and we're not even doing any other work as of yet. As we found out in a [previous optimization post]({{< ref "2013-04-16-adventures-in-optimization-re-typed-racket.md" >}}), we can do a heck of a lot of relatively complex mathematics in 20 ms, so perhaps we can do better?

Well, the main problem is the overhead involved in continuations, so we really can't. Each time we use `call-with-current-continuation`, we have to copy the entire stack and any variables so that we can resume the state. Every time we use it, we have to make another copy, just in case we want to resume that same continuation more than once (it's really quite a powerful construct). There are forms of continuations that we could use instead, limiting either how much we have to remember or how often we can reset to that point, but that's beyond the scope of this post. Perhaps another day. 

If you'd like to see all of the code in one place, you can do so here:
- <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/continuation-thread-pool.rkt">continuation thread pool on GitHub</a>

That code also contains a series of `(module+ test ...)` blocks, each of which can be run with `raco test continuation-thread-pool.rkt`. That's such nice functionality, it's a shame I'm just finding out about it now.

[^1]: I still stand by the saying that [[wiki:Monad|monads]]() are black magic...
[^2]: Actually, just replacing the list with a queue would remove the need for both data structures since we could take threads from one end and push them on the other. But queues aren't built in to most Schemes.
[^3]: And immediately break it, because infinite loop...
[^4]: John McCarthy. A Basis for a Mathematical Theory of Computation. In *Computer Programming And Formal Systems* by P. Braffort and D. Hirschberg (Ed.), 1963.
[^5]: That was one of the original requirements after all.
---
title: Prime Partitions
date: 2012-10-20 14:00:52
programming/languages:
- Racket
- Scheme
programming/sources:
- Programming Praxis
programming/topics:
- Mathematics
- Prime Numbers
---
Today we're back into the mathy sort of problems from Programming Praxis, <a href="http://programmingpraxis.com/2012/10/19/prime-partitions/" title="Programming Praxis: Prime Partitions">tasked with</a> calculating the number of <a href="http://mathworld.wolfram.com/PrimePartition.html" title="WolframMathworld: Prime Partition">prime partitions</a> for a given number--essentially, how many different lists of prime numbers are there that sum to the given number. 

For example, working with 11, there are six prime partitions (I'll show the code for this later):

```scheme
> (prime-partitions 11)
'((2 2 2 2 3) (2 2 2 5) (2 2 7) (2 3 3 3) (3 3 5) (11))
```

Unfortunately, the number of prime partitions quickly gets ridiculous. Once you get to 1000, there are 48 quadrillion prime partitions... So generating all of them isn't exactly feasible.

<!--more-->

Luckily, there's a direct (albeit recursive) formula for calculating the number of prime partitions without actually finding all of them:

{{< latex >}}\kappa(n) = \frac{1}{n} ( sopf(n) + \sum^{n-1}_{j=1} sopf(j) * \kappa(n - j)){{< /latex >}}

That's all well and good, but what in the world is `sopf`? Simply put, it's the sum of (unique) prime factors of a number. So if you have a number like 42, the prime factors are 2, 3, and 7. So `sopf(42) = 12`. Likewise, 12's prime factors are 2, 2, and 3 but we only want unique values, so `sopf(12) = 2 + 3 = 5`.

With that, we could directly calculate the value for {{< inline-latex "\kappa(1000)" >}}:

{{< latex >}}\kappa(1000) = \frac{1}{1000} ( sopf(1000) + \sum^{999}{j=1} sopf(j) * \kappa(1000 - j)) = 48278613741845757{{< /latex >}}

But that's no fun (if still possible) to work out by hand, so let's write a Racket program to do it for us. Luckily, Racket gives us `for/sum`. That means that the definition of `kappa` is rather straight forward: 

```scheme
; determine the number of prime partitions of a number directly
(define (kappa n)
  (* (/ 1 n)
     (+ (sopf  n)
        (for/sum ([j (in-range 1 n)])
          (* (sopf j) (kappa (- n j)))))))
```

To calculate that, we need `sopf`:

```scheme
; calculate the sum of unique prime factors of a number
(define (sopf n)
  (apply + (unique (prime-factors n))))
```

Which of course means we need a way to calculate `prime-factors` (I think I've written `unique` enough times by now):

```scheme
; does m divide into n evenly?
(define (divides? n m)
  (= 0 (remainder n m)))

; return a list of the prime factors of n
(define (prime-factors n)
  (define rootn (sqrt n))
  (cond
    [(<= n 1) '()]
    [(divides? n 2)
     (cons 2 (prime-factors (/ n 2)))]
    [else
     (let loop ([i 3])
       (cond
          [(> i rootn) (list n)]
          [(divides? n i)
           (cons i (prime-factors (/ n i)))]
          [else
           (loop (+ i 2))]))]))
```

A bit longer, but it's a really straight forward algorithm. Simply find the smallest prime factor of a given number then use recursion to find the prime factors of the rest. It does optimize slightly by openly checking up to the square root of n and by only checking odd numbers after 3.

And that's all you need. You can now use `kappa` to directly calculate the number of prime partitions for any number.

To test it, we can compare against the list given on the <a href="http://mathworld.wolfram.com/PrimePartition.html" title="WolframMathWorld: Prime Partitions">WolframMathWolf article</a> on prime partitions: 

```scheme
> (for/list ([i (in-range 2 21)]) (kappa i))
'(1 1 1 2 2 3 3 4 5 6 7 9 10 12 14 17 19 23 26)
```

Unfortunately, the code we've written is *really* slow. 

```scheme
> (time (for/list ([i (in-range 2 21)]) (kappa i)))
cpu time: 2545 real time: 2769 gc time: 85
'(1 1 1 2 2 3 3 4 5 6 7 9 10 12 14 17 19 23 26)
```

If it takes 2.5 seconds to calculate the first 20 values of `kappa`, I'm not even going to try `(kappa 1000)`. It's pretty much the equivalent of writing Fibonacci like this:

```scheme
(define (fib n)
  (cond
    [(< n 1) 1]
    [else (+ (fib (- n 1)) (fib (- n 2)))]))
```

(Don't do that!)

Since each call to `kappa` relies on n-1 other calls to `kappa`, the runtime quickly spirals into an out of control exponential runtime. Wouldn't it be nice if we could just remember each smaller value of `kappa` as we calculate it so we don't have to do all that work over and over? [[wiki:Memoization]]() to the rescue! It turns out that there's already a [my own]({{< ref "2012-10-20-memoization-in-racket.md" >}}) (check it out if you're interested in Scheme macros, it's not too complicated). 

Luckily, it's just a matter of swapping `define-memoized` for `define` in `kappa` and optionally `sopf`. Really, that's all you need. (I renamed them to `msopf` and `mkappa` so I could test both.)

```scheme
> (time (for/list ([i (in-range 2 21)]) (mkappa i)))
cpu time: 1 real time: 0 gc time: 0
'(1 1 1 2 2 3 3 4 5 6 7 9 10 12 14 17 19 23 26)
```

1 ms is just a bit better than 2.5 seconds, wouldn't you say? :smile: And it should scale almost linearly with `n`, so now `(kappa 1000)` shouldn't be a problem:

```scheme
> (time (mkappa 1000))
cpu time: 505 real time: 507 gc time: 20
48278613741845757
```

Half a second and exactly the answer we were looking for. None too shabby.

If you'd like to download the code for this post, you can do so here:

* [prime-partitions source code](https://github.com/jpverkamp/small-projects/blob/master/blog/prime-partitions.rkt "Source for prime-partitions")
* [memoize source code](https://github.com/jpverkamp/small-projects/blob/master/racket-libraries/memoize.rkt "memoize source code")


* * *

As a side note, this problem was particularly problematic at times to debug. Believe it or not, fully formed, correct source code doesn't just spring from my finger tips. For the longest time, I couldn't figure out why all of my `kappa` values were just slightly off and I couldn't figure out why... It turned out that I had a very minor error in `prime-factors`. For any number less than or equal to 1, it would return an invalid list, so `(kappa 1)` wasn't returning the right result. It took longer than I'd care to admit to track the error back to `prime-factors` though, but that's debugging.

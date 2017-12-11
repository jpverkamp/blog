---
title: Smallest consecutive four-factor composites
date: 2013-09-19 14:00:23
programming/languages:
- Racket
- Scheme
programming/sources:
- Programming Praxis
programming/topics:
- Prime Numbers
---
<a href="http://programmingpraxis.com/2013/09/17/smallest-consecutive-four-factor-composites/">Another post</a> from Programming Praxis, from this past Tuesday:

> The smallest pair of consecutive natural numbers that each have two distinct prime factors are 14 = 2 * 7 and 15 = 3 * 5. The smallest triplet of consecutive natural numbers that each have three distinct prime factors are 644 = 2^2 * 7 * 23, 645 = 3 * 5 * 43 and 646 = 2 * 17 * 19. What is the smallest set of four consecutive natural numbers that each have four distinct prime factors?

<!--more-->

Looks straight forward enough. Although when I first read the problem, I thought that the factors had to be unique between the different numbers, which makes it a bit more interesting. I'll solve that problem as well towards then end.

But directly on target, let's generalize somewhat. Say we want to find the `n` consecutive numbers with exactly `m` factors each. So the examples above would be `(2, 2)` and `(3, 3)` while our target is `(4, 4)`. But with this extension, we could look for the first pair with 10 prime factors--`(2, 10)`--or anything else. 

To get that far, the basic idea is to keep a running count of how many consecutive numbers we've seen with the right number of factors. Once we've seen `n` of them, return. If we haven't and we see another, increment. If we haven't, reset because we don't have a run. In terms of code:

```scheme
(require math/number-theory)

(define (prime-factors n)
  (map first (factorize n)))

(define (n-consecutive-with-m-factors n m)
  (let loop ([i 1] [count 0])
    (cond
      [(= count n) 
       (map (λ (n) (list n (factorize n)))
            (range (- i n) i))]
      [(= (length (prime-factors i)) m)
       (loop (+ i 1) (+ count 1))]
      [else 
       (loop (+ i 1) 0)])))
```

The only mildly complicated part is the first term of the `cond` case. That's just so we can output each of the `n` consecutive numbers along with their factors. For example:

```scheme
> (n-consecutive-with-m-factors 2 2)
'((14 ((2 1) (7 1))) 
  (15 ((3 1) (5 1))))
```

That means that the first 2 consecutive numbers with two factors are `14 = 2<sup>1</sup> + 7<sup>1</sup>` and `15 = 3<sup>1</sup> + 5<sup>1</sup>`. 

Likewise:

```scheme
> (n-consecutive-with-m-factors 3 3)
'((644 ((2 2) (7 1) (23 1)))
  (645 ((3 1) (5 1) (43 1)))
  (646 ((2 1) (17 1) (19 1))))
```

And finally, we can run the full `(4, 4)` test:

```scheme
> (time (n-consecutive-with-m-factors 4 4))
cpu time: 3838 real time: 3878 gc time: 139
'((134043 ((3 1) (7 1) (13 1) (491 1)))
  (134044 ((2 2) (23 1) (31 1) (47 1)))
  (134045 ((5 1) (17 1) (19 1) (83 1)))
  (134046 ((2 1) (3 2) (11 1) (677 1))))
```

Four seconds seem a bit much though. Let's see if we can't speed it up. Remember how we've done that each time [in the past]({{< ref "2012-11-01-the-sum-of-the-first-billion-primes.md" >}}) with primes? By {{< wikipedia page="Prime sieve" text="sieving" >}}. Basically, we'll sieve like we always do for primes. But every time we get to a multiple, we don't just mark it as not prime, we also count up how many times we've visited it. This will be the number of unique prime factors. That way, as soon as we see a consecutive sequence, we're done. Something like this:

```scheme
(define (n-consecutive-with-m-factors-sieved n m #:upper-bound [upper-bound 1000000])
  (define n-range (range n))
  (define sieve (make-vector upper-bound 0))
  (let loop ([i 2])
    ; Sieve but only on primes
    (when (zero? (vector-ref sieve i))
      (let loop ([j (+ i i)])
        (when (< j (vector-length sieve))
          (vector-set! sieve j (+ 1 (vector-ref sieve j)))
          (loop (+ j i)))))

    ; Check for consecutive primes
    (cond
      [(andmap (λ (Δ) (= (vector-ref sieve (+ i Δ)) m)) n-range)
       (map (λ (n) (list n (factorize n)))
            (range i (+ i n)))]
      [else
       (loop (+ i 1))])))
```

This one runs significantly more quickly:

```scheme
> (time (n-consecutive-with-m-factors-sieved 4 4))
cpu time: 858 real time: 867 gc time: 47
'((134043 ((3 1) (7 1) (13 1) (491 1)))
  (134044 ((2 2) (23 1) (31 1) (47 1)))
  (134045 ((5 1) (17 1) (19 1) (83 1)))
  (134046 ((2 1) (3 2) (11 1) (677 1))))
```

About four times as fast. That's much better. Unfortunately, it still can't tell us `(2, 10)`, since that doesn't happen in the first 50,000,000 primes and we can't actually go higher than that. So it goes.

That's enough for the problem, but let's go back to my original misinterpretation. How do we look for the first `n` consecutive numbers with `m` **distinct** prime factors? This time we have to keep around the previous factors. We'll use Racket's {{< doc racket "sets" >}} to make finding the unique factors easy, keeping the entire list of `n` previous factors, popping the oldest off each time. Something like this:

```scheme
(define (n-consecutive-with-m-distinct-factors n m)
  (let loop ([i (+ n 2)]
             [factors (map (λ (Δ) (list->set (prime-factors (+ n 2 Δ)))) (range n))])
    (cond
      [(= m (set-count (apply set-union factors)))
       (map (λ (n) (list n (factorize n)))
            (range (- i n) i))]
      [else
       (loop (+ i 1)
             (append (rest factors)
                     (list (list->set (prime-factors (+ i 1))))))])))
```

Straight forward. With this we can find the first pair with 2-10 **distinct** prime factors:

```scheme
> (n-consecutive-with-m-distinct-factors 2 2)
'((2 ((2 1))) (3 ((3 1))))
> (n-consecutive-with-m-distinct-factors 2 3)
'((4 ((2 2))) (5 ((5 1))))
> (n-consecutive-with-m-distinct-factors 2 4)
'((13 ((13 1))) (14 ((2 1) (7 1))))
> (n-consecutive-with-m-distinct-factors 2 5)
'((64 ((2 6))) (65 ((5 1) (13 1))))
> (n-consecutive-with-m-distinct-factors 2 6)
'((208 ((2 4) (13 1))) (209 ((11 1) (19 1))))
> (n-consecutive-with-m-distinct-factors 2 7)
'((713 ((23 1) (31 1))) (714 ((2 1) (3 1) (7 1) (17 1))))
> (n-consecutive-with-m-distinct-factors 2 8)
'((7313 ((71 1) (103 1))) (7314 ((2 1) (3 1) (23 1) (53 1))))
> (n-consecutive-with-m-distinct-factors 2 9)
'((38569 ((38569 1))) (38570 ((2 1) (5 1) (7 1) (19 1) (29 1))))
> (n-consecutive-with-m-distinct-factors 2 10)
'((254539 ((331 1) (769 1))) (254540 ((2 2) (5 1) (11 1) (13 1) (89 1))))
```

That actually runs significantly faster, mostly since we're not as limited in the number of factors each number has. That means that there is a lot more candidates. 

And that's all we have for today. As always, the full code (along with a pile of unit tests that takes a few minutes to run) is available on GitHub: <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/consecutive-factors.rkt">jpverkamp/consecutive-factors</a>.

As a random bonus, I was playing with Racket's plotting library to see just how quickly this things grow. It's pretty impressive:

```scheme
(require plot)

(define values
  (for*/list ([x (in-range 2 10)]
              [y (in-range 2 10)])
    (with-handlers ([exn? (λ (_) #f)])
      (vectir x y (caar (n-consecutive-with-m-factors-sieved x y))))))

(plot3d 
 (discrete-histogram3d 
  (filter (λ (x) x) values)
  #:color 4 #:line-color 4))
```

{{< figure src="/embeds/2013/consecutive-factors.png" >}}

Basically, all it says is that these things grow wicked fast. The `x axis` is the number of consecutive values we're looking for, while the `y axis` is how many prime factors we need. `(2, 5)` is already almost off the charts... I think the most interesting part is that `(2, 9)` is out of bounds (therefore at least over 1,000,000). Up until then, we find large clusters with two primes. But at 9, they're further apart.
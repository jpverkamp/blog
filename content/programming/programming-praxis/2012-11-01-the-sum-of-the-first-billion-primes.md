---
title: The Sum Of The First Billion Primes
date: 2012-11-01 14:00:03
programming/languages:
- Racket
- Scheme
programming/sources:
- Programming Praxis
programming/topics:
- Mathematics
- Prime Numbers
---
<a title="Programming Praxis: The Sum of the First Billion Primes" href="http://programmingpraxis.com/2012/09/11/the-sum-of-the-first-billion-primes/">This problem</a> from Programming Praxis came about in the comments to my last post and intrigued me. So today, we are trying to sum the first one billion primes. Summing the first hundred, thousand, even million primes isn't actually that bad. But it takes a bit more effort when you scale it up to a billion. And why's that?

<!--more-->

Before I get started, if you'd like to download today's source code and follow along, you can do so here: <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/billion-primes.rkt" title="billion primes source">billion primes source</a>

Now that that's out of the way, the first problem is time. A naive approach would be to go through all of the numbers from 2 to a billion and test if each is prime. To do that, test each number up to your current number and see if the latter divides the former. Simple enough:

```scheme
; test if n divides m
(define (divides? m n)
  (= 0 (remainder m n)))

; test if n is prime by trial division
(define (prime? n)
  (and (not (divides? n 2))
       (for/and ([i (in-range 3 (+ 1 (ceiling (sqrt n))) 2)])
         (not (divides? n i)))))

; sum the first n primes directly
(define (sum-primes-direct n)
  (let loop ([i 3] [count 1] [sum 2])
    (cond
      [(= count n) sum]
      [(prime? i)
       (loop (+ i 2) (+ count 1) (+ sum i))]
      [else
       (loop (+ i 2) count sum)])))
```

Not too bad, we can sum the first hundred thousand primes pretty easily:

```scheme
> (time (sum-primes-direct 100000))
cpu time: 3068 real time: 3063 gc time: 79
62260698721
```

If we waited a bit longer, we could even get the first billion that way. Still, that's 3 seconds for just only 1/10,000th of the problem. I think that we can do better. What's the next idea? Perhaps if rather than dividing by all numbers from 2 up to the number we're dealing with, why don't we just divide by the previous primes:

```scheme
; sum the first n primes by keeping a list of primes to divide by
(define (sum-primes-list n)
  (let loop ([i 3] [count 1] [sum 2] [primes '()])
    (cond
      [(= count n)
       sum]
      [(andmap (lambda (prime) (not (divides? i prime))) primes)
       (loop (+ i 2) (+ count 1) (+ sum i) (cons i primes))]
      [else
       (loop (+ i 2) count sum primes)])))
```

Simple enough. And theoretically it should be faster, yes? After all, we're doing far fewer divisions for each number. But no. It turns out that it's not actually faster at all. If you cut it down to the first 10,000 primes, the direct solution only takes 91 ms but this solution takes a whopping 9 seconds. That's two whole orders of magnitude. Ouch!

```scheme
> (time (sum-primes-direct 10000))
cpu time: 91 real time: 90 gc time: 0
496165411

> (time (sum-primes-list 10000))
cpu time: 8995 real time: 8987 gc time: 0
496165411
```

At first, you might think that that doesn't make the least bit of sense. After all, we're doing essentially the same thing, we're just performing fewer divisions. So why isn't it faster?

Basically, it all comes down to memory access. In the first direct case, we basically aren't using the system's RAM. Everything (or just about) can be done in registers directly on the CPU. In the second case though, there's constant swapping as the list grows too large to hold in registers alone. And memory access is orders of magnitude slower than any single instruction on the CPU. Really, this is a perfect example of both this phenomenon and the cost of premature optimization. Just because something should be faster according to runtime alone, that's not the entire story.

Still, we're not quite done. I know we can do better than the direct method. So this time, let's use a more intricate method, specifically the [[wiki:Sieve of Eratosthenes]](). The basic idea is to start with a list of all of the numbers you are interested in. Then repeatedly take the first number as prime and cross out all of it's multiples. There's a pretty nice graphic on the aforelinked Wikipedia page.

And if we just go with a loop, the code is rather straight forward:

```scheme
; sum the first n primes using the Sieve of Eratosthenes
; algorithm source: http://en.wikipedia.org/wiki/Sieve_of_Eratosthenes
(define (sum-primes-sieve-eratosthenes-list n)
  (define-values (lo hi) (guess-nth-prime n))
  (let loop ([ls (range 2 hi)]
             [count 0]
             [sum 0])
    (cond
      [(= count n) sum]
      [else
       (loop 
        (filter
         (lambda (i) (not (divides? i (car ls))))
         (cdr ls))
        (+ count 1)
        (+ (car ls) sum))])))
```

There's one interesting bit--the `guess-nth-prime` function:

```scheme
; estimate the nth prime, return lower and upper bounds
; source: http://en.wikipedia.org/wiki/Prime_number_theorem
(define (guess-nth-prime n)
  (values (inexact->exact 
           (floor (* n (log n))))
          (inexact->exact 
           (ceiling
            (if (<= n 1) 
                3 
                (+ (* n (log n)) (* n (log (log n)))))))))
```

By default, the Sieve of Eratosthenes generates all of the primes from 1 to some number n. But that's not what we want. Instead, we want the first n primes. After a bit of searching though, I found the Wikipedia page on the [[wiki:Prime number theorem]](). That defines the function `pi(n)` which approximates the number of primes less than or equal to n. Invert that function and you find that the value of the nth prime p<sub>n</sub> falls in the range:

{{< latex >}}n * ln(n) < p_n < n * ln(ln(n)){{< /latex >}}

That upper bound is the one that lets us generate enough primes with the [[wiki:Sieve of Eratosthenes]]() so that we can sum the first n. 

The best part is that it turns out that it's at least faster than the list based method:

```scheme
> (time (sum-primes-sieve-eratosthenes-list 10000))
cpu time: 4347 real time: 4344 gc time: 776
496165411
```

Still. That's not good enough. The problem here is much the same as the list based method. We're passingly along and constantly building a list that would eventually have a billion elements in it. Not something that's particularly easy to deal with. So instead of a list, why don't we use a vector of `#t`/`#f`?

```scheme
; sum the first n primes using the Sieve of Eratosthenes with a vector
; algorithm source: http://en.wikipedia.org/wiki/Sieve_of_Eratosthenes
(define (sum-primes-sieve-eratosthenes-vector n)
  (define-values (lo hi) (guess-nth-prime n))
  (define v (make-vector hi #t))
  (vector-set! v 0 #f)
  (vector-set! v 1 #f)
  (for* ([i (in-range 2 hi)]
         #:when (vector-ref v i)
         [j (in-range (* i i) hi i)])
    (vector-set! v j #f))
  (let loop ([i 3] [count 1] [sum 2])
    (cond
      [(= count n) sum]
      [(vector-ref v i)
       (loop (+ i 2) (+ count 1) (+ sum i))]
      [else
       (loop (+ i 2) count sum)])))
```

So how does it perform?

```scheme
> (time (sum-primes-sieve-eratosthenes-vector 10000))
cpu time: 6 real time: 6 gc time: 0
496165411
```

Dang that's nice. :smile: Let's scale to a million:

```scheme
> (time (sum-primes-sieve-eratosthenes-vector 1000000))
cpu time: 892 real time: 889 gc time: 2
7472966967499
```

Less than a second isn't too shabby. It's slower than I'd like, but I could wait a thousand seconds (a bit over 16 minutes) if I had to.

```scheme
> (time (sum-primes-sieve-eratosthenes-vector 1000000000))
out of memory
```

Oops. It turns out that calling `make-vector` to make a billion element vector doesn't actually work so well on my machine... We're going to have to get a get a little sneakier.

Perhaps if we used the bitvectors from [Monday's post]({{< ref "2012-10-29-bitvectors-in-racket.md" >}})? (And now you know why I made that library :smile:). All we have to do is swap out each instance of `make-vector`, `vector-ref`, or `vector-set!` for `make-bitvector`, `bitvector-ref`, or `bitvector-set!`.

```scheme
> (time (sum-primes-sieve-eratosthenes-bitvector 1000000))
cpu time: 5174 real time: 5170 gc time: 0
7472966967499
```

So it run about five times slower than the simple vector based method (which makes sense if you think about it; twiddling bits doesn't come for free). Still, we're using a fair bit less memory. Let's see if it can handle a billion:

```scheme
> (time (sum-primes-sieve-eratosthenes-bitvector 1000000000))
cpu time: 9724165 real time: 9713671 gc time: 5119
11138479445180240497
```

Dang. Nice. 2 hrs 41 minutes may be more than twice as long as I was expecting based on the 16 minute estimate for the one million run `vector` version and the 5x slowdown between the `vector` and `bitvector` versions. Still, it worked. And that's a pretty good base all by itself. Still, I think we can do better. 

Upon some searching, it turns out that you can actually create vectors containing one billion entries. You just can't have them all in the same vector. So instead, I created another datatype: the `multivector`. Essentially, the idea is to create several smaller vectors and abstract the `ref` and `set!` methods to minimize the changes to the Sieve of Eratosthenes code. 

```scheme
(define-struct multivector (size chunks default data)
  #:mutable
  #:constructor-name make-multivector-struct)

(define (make-multivector size [chunks 1] [default #f])
  (define per-chunk (inexact->exact (ceiling (/ size chunks))))
  (make-multivector-struct
   size chunks default
   (for/vector ([i (in-range chunks)])
     (if (= i (- chunks 1))
         (make-vector (- size (* (- chunks 1) per-chunk)) default)
         (make-vector per-chunk default)))))

(define (multivector-ref mv i)
  (vector-ref (vector-ref (multivector-data mv)
                          (quotient i (multivector-chunks mv)))
              (remainder i (multivector-chunks mv))))

(define (multivector-set! mv i v)
  (vector-set! (vector-ref (multivector-data mv)
                           (quotient i (multivector-chunks mv)))
               (remainder i (multivector-chunks mv))
               v))
```

You can test it if you'd like, but it does work. So let's try it in the Sieve of Eratosthenes. The same as before, just swap out `make-vector`, `vector-ref`, or `vector-set!` for `make-multivector`, `multivector-ref`, or `multivector-set!`.

So how does the performance compare? 

```scheme
> (time (sum-primes-sieve-eratosthenes-multivector 1000000))
cpu time: 6635 real time: 6625 gc time: 435
7472966967499
```

Hmm. Well, it doesn't actually run any faster than the `bitvector`, but it also doesn't run out of memory. 

I think we may have a winner, but before we wind down, there are two other sieves linked to from the Sieve of Eratosthenes page: the [[wiki:Sieve of Atkin]]() and the [[wiki:Sieve of Sundaram]](). The algorithms are a bit more complicated than the Sieve of Eratosthenes, but still entirely doable. It is interesting just how they work though. The Sieve of Eratosthenes is intuitive. These two? A bit less so. 

First, we have the [[wiki:Sieve of Atkin]]():

```scheme
; sum the first n primes using the Sieve of Atkin
; algorithm source: http://en.wikipedia.org/wiki/Sieve_of_Atkin
(define (sum-primes-sieve-atkin n)
  (define-values (lo hi) (guess-nth-prime n))
  (define v (make-vector hi #f))
  ; add candidate primes
  (for* ([x (in-range 1 (+ 1 (sqrt hi)))]
         [y (in-range 1 (+ 1 (sqrt hi)))])
    (define x2 (* x x))
    (define y2 (* y y))
    (let ([i (+ (* 4 x2) y2)])
      (when (and (< i hi) (or (= 1 (remainder i 12))
                               (= 5 (remainder i 12))))
        (vector-set! v i (not (vector-ref v i)))))
    (let ([i (+ (* 3 x2) y2)])
      (when (and (< i hi) (= 7 (remainder i 12)))
        (vector-set! v i (not (vector-ref v i)))))
    (let ([i (- (* 3 x2) y2)])
      (when (and (> x y) (< i hi) (= 11 (remainder i 12)))
        (vector-set! v i (not (vector-ref v i))))))
  ; remove composites
  (for ([i (in-range 5 (+ 1 (sqrt hi)))])
    (when (vector-ref v i)
      (for ([k (in-range (* i i) hi (* i i))])
        (vector-set! v k #f))))
  ; report
  (let loop ([i 5] [count 2] [sum 5])
    (cond
      [(= count n) sum]
      [(vector-ref v i)
       (loop (+ i 2) (+ count 1) (+ sum i))]
      [else
       (loop (+ i 2) count sum)])))
```

It's pretty much a direct translation of the code on the Wikipedia page. Since it uses `vector`, it won't be able to calculate the sum of the first billion, but you could pretty easily replace swap out for a `bitvector` or `multivector`. Still, I'm mostly interested in the implementation and performance to start with. Speaking of which: 

```scheme
> (time (sum-primes-sieve-atkin 1000000))
cpu time: 2421 real time: 2421 gc time: 415
7472966967499
```

So this particular version is about three times slower than the vector version of the Sieve of Eratosthenes. The Wikipedia page mentions that there are a number of optimizations that you could do to speed this up which I may try some day, but not today. What's interesting though is that if you do swap out a `bitvector` for a vector, it's actually faster:

```scheme
> (time (sum-primes-sieve-atkin-bitvector 1000000))
cpu time: 3059 real time: 3058 gc time: 0
7472966967499
```

If that proportion follows through to the billion element run, we should be able to finish in just an hour and a half. Let's try it out.

```scheme
> (time (sum-primes-sieve-atkin-bitvector 1000000000))
cpu time: 5304855 real time: 5300800 gc time: 1237
11138479445180240497
```

An hour and a half, spot on. None too shabby if I do say so myself. (Although I bet we could get even faster. I'll leave that as an exercise for another day though.)

Finally, the Sieve of Sundaram. This one is even more different than the previous ones, not removing multiples of primes but rather removing all composites less than *n* by noting that they all have the form *i + j + 2ij &le; n*:

```scheme
; sum the first n primes using the Sieve of Sundaram
; algorithm source: http://en.wikipedia.org/wiki/Sieve_of_Sundaram
(define (sum-primes-sieve-sundaram n)
  (define-values (lo hi) (guess-nth-prime n))
  (define dn (quotient hi 2))
  (define v (make-vector dn #t))
  (for* ([j (in-range 1 dn)]
         [i (in-range 1 (+ j 1))]
         #:when (< (+ i j (* 2 i j)) dn))
    (vector-set! v (+ i j (* 2 i j)) #f))
  (let loop ([i 1] [count 1] [sum 2])
    (cond
      [(= count n) sum]
      [(vector-ref v i)
       (loop (+ i 1) (+ count 1) (+ sum (+ 1 (* 2 i))))]
      [else
       (loop (+ i 1) count sum)])))
```

Very straight forward code, how does it perform?

```scheme
> (time (sum-primes-sieve-sundaram 10000))
cpu time: 32066 real time: 32055 gc time: 0
496165411
```

Eesh. Note that that's only on 10,000 and it still took 30 seconds. I think I'll skip running this one even out to a million.

Well, that's enough for today I think. Here's a nice timing summary for the methods:


|                           **Algorithm**                           | **Ten thousand** | **One million** | **One billion** |
|-------------------------------------------------------------------|------------------|-----------------|-----------------|
|                              Direct                               |      91 ms       |     86.0 s      |        —        |
|                          Previous primes                          |      9.0 s       |        —        |        —        |
|                        Eratosthenes (list)                        |      4.3 s       |        —        |        —        |
|                       Eratosthenes (vector)                       |       6 ms       |      0.9 s      |        —        |
|                     Eratosthenes (bitvector)                      |      31 ms       |      5.2 s      |   2 hr 42 min   |
|                    Eratosthenes (multivector)                     |      34 ms       |      6.6 s      |        —        |
|                          Atkin (vector)                           |      12 ms       |      2.4 s      |        —        |
|                         Atkin (bitvector)                         |      20 ms       |      3.1 s      |   1 hr 28 min   |
|                        Atkin (multivector)                        |      23 ms       |      4.4 s      |        —        |
|                             Sundaram                              |      32.1 s      |        —        |        —        |
| [Segmented Sieve]({{< ref "2012-11-29-one-billion-primes-segmented-sieve.md" >}}) |       7 ms       |      0.9 s      |  25 min 12 sec  |


And the actual values:


| **Ten thousand** |      496165411       |
|------------------|----------------------|
| **One million**  |    7472966967499     |
| **One billion**  | 11138479445180240497 |


If you'd like to download the source code for today's post, you can do so here:
- <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/billion-primes.rkt" title="billion primes source">billion primes source</a>
- <a href="https://github.com/jpverkamp/small-projects/blob/master/racket-libraries/bitvector.rkt" title="bitvector source">bitvector source</a>
- <a href="https://github.com/jpverkamp/small-projects/blob/master/racket-libraries/multivector.rkt" title="multivector source">multivector source</a>

**Edit**: After Will's comments, I actually got around to writing a segmented version. It's pretty amazing the different it made too. It runs about 3x faster than even the Sieve of Atkin. Sometimes optimization is awesome. You can find that post [here]({{< ref "2012-11-29-one-billion-primes-segmented-sieve.md" >}}) and the source code <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/billion-primes-segmented.rkt" title="GitHub: Segmented billion primes source">here</a>.

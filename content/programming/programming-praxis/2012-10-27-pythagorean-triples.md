---
title: Pythagorean Triples
date: 2012-10-27 14:00:44
programming/languages:
- Racket
- Scheme
programming/sources:
- Programming Praxis
programming/topics:
- Mathematics
---
When Programming Praxis mentioned that the <a href="http://programmingpraxis.com/2012/10/26/pythagorean-triples/" title="Programming Praxis: Pythagorean Triples">newest challenge</a> sounded like a <a href="http://projecteuler.net/" title="Project Euler">Project Euler</a> problem, they were't wrong. Basically, the idea is to count the number of {{< wikipedia "Pythagorean Triples" >}} with perimeters (sum of the three numbers) under a given value. The necessary code to brute force the problem is really straight forward, but then they asked for the count up to one million. With the brute force {{< inline-latex "O(n^2)" >}} algorithm (and a relatively high constant), that's not really feasible. So that's when we have to get a bit more creative.

<!--more-->

First, how about that brute force solution I promised:

```scheme
(define (brute-count-triples-under sum)
  (define count 0)
  (for* ([a (in-range 1 sum)]
         [b (in-range 1 a)]
         #:when (let ([c (sqrt (+ (* a a) (* b b)))])
                  (and (<= (+ a b c) sum)
                       (integer? c))))
    (set! count (+ count 1)))
  count)
```

The basic idea is calculate every a and b such that a < b and such that {{< inline-latex "c = \sqrt{a^2 + b^2}" >}} for some integer c and the sum a+b+c is less than the target. Simple enough, how does that work out?

```scheme
> (time (brute-count-triples-under 100))
cpu time: 8 real time: 5 gc time: 0
17
```

And pretty fast too. But if we try to run longer examples:

```scheme
> (time (brute-count-triples-under 1000))
cpu time: 584 real time: 585 gc time: 48
325

> (time (brute-count-triples-under 10000))
cpu time: 54687 real time: 54840 gc time: 1348
4858
```

Yeah, I don't really want to try that on one million. So we need a faster algorithm. Luckily, you don't have to try all of the possible ways that could generate a triple--it turns out there are algorithms to {{< wikipedia page="Formulas for generating Pythagorean triples" text="do it for you" >}}. One in particularly came from a British math professor A. Hall in the paper *<a href="http://www.jstor.org/discover/10.2307/3613860?uid=2&uid=4&sid=21101204896923" title="Genealogy of Pythagorean Triads">Genealogy of Pythagorean Triads</a>* which showed that given any primitive Pythagorean triple (one that is not a multiple of another, smaller triple), you can produce three more primitive triples with the formulas:


> a – 2b + 2c, 2a – b + 2c, 2a – 2b + 3c
> a + 2b + 2c, 2a + b + 2c, 2a + 2b + 3c
> -a + 2b + 2c, -2a + b + 2c, -2a + 2b + 3c


You can generate even more primitive triples from those in turn, as long as you choose to do so. In our case, we can stop each branch once the perimeter of the triple is larger than our target as they don't ever get smaller. So how do we turn that into code? We use Racket's {{< doc racket "generators" >}}: 

```scheme
(define (primitive-triples [max-sum #f])
  (generator ()
    (let loop ([a 3] [b 4] [c 5])
      (when (or (not max-sum) (<= (+ a b c) max-sum))
        (yield (list (min a b) (max a b) c))
        ; a – 2b + 2c, 2a – b + 2c, 2a – 2b + 3c
        (loop (+ a (* -2 b) (* 2 c))
              (+ (* 2 a) (- b) (* 2 c))
              (+ (* 2 a) (* -2 b) (* 3 c)))
        ; a + 2b + 2c, 2a + b + 2c, 2a + 2b + 3c
        (loop (+ a (* 2 b) (* 2 c))
              (+ (* 2 a) b (* 2 c))
              (+ (* 2 a) (* 2 b) (* 3 c)))
        ; -a + 2b + 2c, -2a + b + 2c, -2a + 2b + 3c
        (loop (+ (- a) (* 2 b) (* 2 c))
              (+ (* -2 a) b (* 2 c))
              (+ (* -2 a) (* 2 b) (* 3 c)))))
    (yield #f)))
```

Similar to Python's `yield`, this generator will create a sequence of primitive triples, scanning in a depth first manner down each branch of the aforementioned tree. From there, we just have to calculate each multiple to get a list of all Pythagorean triples with perimeters less than a given value:

```scheme
(define (triples-under sum)
  (for*/list ([trip (in-producer (primitive-triples sum) #f)]
              [k (in-range 1 (+ 1 (quotient sum (apply + trip))))])
    (map (lambda (n) (* n k)) trip)))
```

So if we wanted to test this with all 17 triples with perimeters under 100, we could:

```scheme
> (triples-under 100)
'((3 4 5)    (6 8 10)   (9 12 15)  (12 16 20) (15 20 25) (18 24 30) (21 28 35)
  (24 32 40) (5 12 13)  (10 24 26) (15 36 39) (7 24 25)  (9 40 41)  (20 21 29)
  (8 15 17)  (16 30 34) (12 35 37))
```

On the other hand though, we don't necessarily care what the actual triples are, we just want to know how many there are. So a slight modification to just count them:

```scheme
(define (count-triples-under sum)
  (define count 0)
  (for* ([trip (in-producer (primitive-triples sum) #f)]
         [k (in-range 1 (+ 1 (quotient sum (apply + trip))))])
    (set! count (+ count 1)))
  count)
```

And that's it. We can finally answer the question originally asked of us:

```scheme
> (time (count-triples-under 1000000))
cpu time: 6116 real time: 6121 gc time: 1792
808950
```

It's still not as fast as I'd like, but it's certainly faster than it would have been without the fancier algorithm. 

And that's all there is to it. If you'd like to download the entire source code for today, you can do so here: <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/pythagorean-triples.rkt">pythagorean-triples source</a>

Like I said before, it definitely did have the feel of a Project Euler problem, where the straight forward solution is not generally the best one and if you work at it, you can find something that will run in a fraction of the time.

Perhaps I'll start publishing my Project Euler solutions here. I've worked through a good chunk of the problems on two separate occasions, both in Python and in Scheme and it might be interesting to compare and contrast the different languages. Although since it's sort of a contest, that might be frowned upon. We'll see. 

**Edit:**

Eesh. When programmingpraxis mentioned that generators were slow down in the comments, I remembered some chatter on the Racket mailing list (the thread from this message) talking about generator performance. But I hadn't realized it would be quite *this* extensive. It's easy enough to reimplement the code to make `primitive-triples` just return a list of all of the triples directly:

```scheme
(define (primitive-triples-nogen max-sum)
  (let loop ([a 3] [b 4] [c 5])
    (if (> (+ a b c) max-sum)
        '()
        (append
         (list (list (min a b) (max a b) c))
         ; a – 2b + 2c, 2a – b + 2c, 2a – 2b + 3c
         (loop (+ a (* -2 b) (* 2 c))
               (+ (* 2 a) (- b) (* 2 c))
               (+ (* 2 a) (* -2 b) (* 3 c)))
         ; a + 2b + 2c, 2a + b + 2c, 2a + 2b + 3c
         (loop (+ a (* 2 b) (* 2 c))
               (+ (* 2 a) b (* 2 c))
               (+ (* 2 a) (* 2 b) (* 3 c)))
         ; -a + 2b + 2c, -2a + b + 2c, -2a + 2b + 3c
         (loop (+ (- a) (* 2 b) (* 2 c))
               (+ (* -2 a) b (* 2 c))
               (+ (* -2 a) (* 2 b) (* 3 c)))))))

(define (count-triples-under-nogen sum)
  (define count 0)
  (for* ([trip (in-list (primitive-triples-nogen sum))]
         [k (in-range 1 (+ 1 (quotient sum (apply + trip))))])
    (set! count (+ count 1)))
  count)
```

Then look at the performance we get:

```scheme
> (time (count-triples-under 1000000))
cpu time: 7109 real time: 7129 gc time: 2292
808950

> (time (count-triples-under-nogen 1000000))
cpu time: 352 real time: 348 gc time: 112
808950
```

Yeah... So there is a bit of a performance penalty for generators after all (most likely due to the use of continuations to implement them according to the aforementioned thread). I'll have to keep that in mind. 

**Edit 2:**

So I decided to go for the best of both worlds and essentially make a generator while maintaining the state myself. Essentially, I'll use `set!` to update the list of triples we haven't yet tried, stored in the function's state.

```scheme
(define (primitive-triples-state [max-sum #f])
  (define triples '((3 4 5)))
  (lambda ()
    (let loop ()
      (cond
        [(null? triples) #f]
        [else
         (define a (caar triples))
         (define b (cadar triples))
         (define c (caddar triples))
         (cond
           [(and max-sum (> (+ a b c) max-sum))
            (set! triples (cdr triples))
            (loop)]
           [else
            (define r (car triples))
            (set! triples
                  (list*
                   ; a – 2b + 2c, 2a – b + 2c, 2a – 2b + 3c
                   (list (+ a (* -2 b) (* 2 c))
                         (+ (* 2 a) (- b) (* 2 c))
                         (+ (* 2 a) (* -2 b) (* 3 c)))
                   ; a + 2b + 2c, 2a + b + 2c, 2a + 2b + 3c
                   (list (+ a (* 2 b) (* 2 c))
                         (+ (* 2 a) b (* 2 c))
                         (+ (* 2 a) (* 2 b) (* 3 c)))
                   ; -a + 2b + 2c, -2a + b + 2c, -2a + 2b + 3c
                   (list (+ (- a) (* 2 b) (* 2 c))
                         (+ (* -2 a) b (* 2 c))
                         (+ (* -2 a) (* 2 b) (* 3 c)))
                   ; all of the rest
                   (cdr triples)))
            r])]))))

(define (count-triples-under-state sum)
  (define count 0)
  (for* ([trip (in-producer (primitive-triples-state sum) #f)]
         [k (in-range 1 (+ 1 (quotient sum (apply + trip))))])
    (set! count (+ count 1)))
  count)
```

It's fractionally slower than the version that just directly returns the list (the overhead of the function calls, I'm guessing), but not enough to be statistically significant.

```scheme
> (time (count-triples-under-nogen 1000000))
cpu time: 352 real time: 348 gc time: 112
808950

> (time (count-triples-under-state 1000000))
cpu time: 388 real time: 388 gc time: 0
808950
```

Now I'm wondering how hard it would be a write a version of the `generator` macro that bundles this all up for you. It wouldn't be as general purpose, but I'm will to bet it could be done.
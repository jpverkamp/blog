---
title: Optimizing Voronoi
date: 2012-09-13 14:00:07
programming/languages:
- Java
- Scheme
---
Starting with my [previous post]({{< ref "2012-09-09-generating-voronoi-diagrams.md" >}}) on Voronoi diagrams, I felt that I could do better. Sure, the code works well enough but it's almost painfully slow. So let's see if we can optimize it a bit.

<!--more-->

First, here's the original code for comparison:

```scheme
(define (fill dist rs cs pts cls)
  (make-image rs cs
    (lambda (r c)
      (cadar
        (sort
          (lambda (pc1 pc2) (< (car pc1) (car pc2)))
          (map (lambda (pt cl)
                 (list (dist (list r c) pt) cl))
            pts cls))))))
```

Basically, for each pixel in the new image we go through and build up a list of distance/color pairs for every reference point, then we sort them, then we choose the first one. But sorting introduces at least an `O(n log n)` cost that we really don't have to pay. So instead of sorting, why don't we keep track of the minimum distance/color as we go?

```scheme
(define (fill-fast dist rs cs pts cls)
  (make-image rs cs
    (lambda (r c)
      (let ([rc (list r c)])
        (let loop ([min-d (dist (car pts) rc)]
                   [min-cl (car cls)]
                   [pts (cdr pts)]
                   [cls (cdr cls)])
          (if (null? pts)
              min-cl
              (let ([new-d (dist (car pts) rc)])
                (if (< new-d min-d)
                    (loop new-d (car cls) (cdr pts) (cdr cls))
                    (loop min-d min-cl (cdr pts) (cdr cls))))))))))
```

Makes sense, but when you're doing straight forward recursion like that, you always should wonder if the code could be written more cleanly with a fold. It turns out:

```scheme
(define (fill-fold dist rs cs pts cls)
  (make-image rs cs
    (lambda (r c)
      (let ([rc (list r c)])
        (fold-left
          (lambda (min-d/cl pt cl)
            (let ([new-d (dist (car pts) rc)])
              (if (< new-d (car min-d/cl))
                  (list new-d cl)
                  min-d/cl)))
          (list (dist (car pts) rc) (car cls))
          (cdr pts)
          (cdr cls))))))
```

Okay, so perhaps it's not necessarily more clean as I ended up wrapping/unwrapping a pair with the distance and color over and over again, but it's still relatively straight forward. While I was at it, I also wrote a version for `fill-fold-right` that used `fold-right` instead of `fold-left` (which also required reordering the arguments as `(pt cl min-d/cl)`).

While I was at it, I also wrote a new distance function. `expt` can handle any exponent so likely can't do the same optimizations that a simple squaring function could do and at the same time, it shouldn't actually be necessary to do the square root as that won't effect the relative ordering of points for anything with a distance over 1 (all of them). So here we have a faster distance function:

```scheme
(define (fast-distance p1 p2)
  (let ([x (- (car p1) (car p2))]
        [y (- (cadr p1) (cadr p2))])
    (+ (* x x) (* y y))))
```

Enough with the code, let's see how it worked! To simplify testing, I wrote a timing macro and a simple test running framework:

```scheme
(define-syntax timed
  (syntax-rules (as)
    [(_ as name bodies ...)
     (let* ([beg (cpu-time)]
            [res (begin bodies ...)])
       (printf "~a: ~a ms\n" name (- (cpu-time) beg))
       res)]))

(define (random-color) (color (random 256) (random 256) (random 256)))

(define (test rs cs n)
  (let* ([pts (map (lambda (_) (list (random rs) (random cs))) (iota n))]
         [cls (map (lambda (_) (random-color)) (iota n))])
    (timed as "original" (fill distance rs cs pts cls))
    (timed as "faster" (fill-fast distance rs cs pts cls))
    (timed as "folded (left)" (fill-fold distance rs cs pts cls))
    (timed as "folded (right)" (fill-fold-right distance rs cs pts cls))
    (timed as "original w/ fast dist" (fill fast-distance rs cs pts cls))
    (timed as "faster w/ fast dist" (fill-fast fast-distance rs cs pts cls))
    (timed as "folded (left) w/ fast dist" (fill-fold fast-distance rs cs pts cls))
    (timed as "folded (right) w/ fast dist" (fill-fold-right fast-distance rs cs pts cls))
    (void)))
```

Let's see what it says, shall we?

```
~ (test 256 256 16)
original: 1844 ms
faster: 1829 ms
folded (left): 1522 ms
folded (right): 1498 ms
original w/ fast dist: 1494 ms
faster w/ fast dist: 1439 ms
folded (left) w/ fast dist: 1081 ms
folded (right) w/ fast dist: 1072 ms
```

Interesting... It turns out that the "faster" fold that I was working on really isn't that much faster at all. Folding (which essentially does the same thing but allows for more optimization) is even faster yet. Yet really it's the faster distance function that saves the day. The best code with the slower distance function is still faster than the worst code with the fastest distance function. It turns out that when you're trying to tune code, the primitives you're working with really matter.

Here's another much larger test set:

```
~ (test 1024 1024 128)
original: 270476 ms
faster: 193126 ms
folded (left): 154777 ms
folded (right): 151224 ms
original w/ fast dist: 220065 ms
faster w/ fast dist: 141528 ms
folded (left) w/ fast dist: 98143 ms
folded (right) w/ fast dist: 95932 ms
```

This time at least the faster function is actually a decent bit faster, although the folded ones continue to dominate. Again though, the faster distance function made a much bigger splash.

As a last note, it's a little unfortunate that this code is even as slow as it is now. It shouldn't take even a second to generate a 256x256 Voronoi diagram, that sort of thing should take perhaps tens of milliseconds, if that. Mostly, it's due to the [C211 image library]({{< ref "2011-08-27-wombat-ide-c211-tree-and-image-libraries.md" >}}). It's designed so that the library code can be both easy to read and portable ([calling between Scheme and Java]({{< ref "2012-02-23-wombat-ide-scheme-java-interop.md" >}}) for the strengths of each). Both unfortunately mean that the library is slower than I'd like. Optimally, I'd work on making it faster, but that's a post for another day.

If you'd like to download the source code, you can do so here: <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/find-in-pi.rkt" title="voronoi source">voronoi source</a>

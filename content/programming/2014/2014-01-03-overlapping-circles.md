---
title: Overlapping circles
date: 2014-01-03 14:00:16
programming/languages:
- Racket
- Scheme
programming/sources:
- L2Program
programming/topics:
- Geometry
- Monte Carlo
---
Here's a quick little programming task that I came to via <a href="http://l2program.co.uk/671/overlapping-circles">a post</a> on L2Program (who in turn seems to have found it on Reddit). The basic idea is to take a given list of circles and to determine the area enclosed (while correctly accounting for overlap).

<!--more-->

It should be possible to calculate this directly / geometrically, but where's the fun in that? :smile: Instead, we'll go with a [[wiki:Monte Carlo simulation]](). Basically, generate a bunch of points and check if each is in any of the circles (much easier to calculate). Use the ratio of hits to misses to calculate the are.

First, we'll start with a few structures to define points and circles:

```scheme
(struct point     (x y)           #:transparent)
(struct circle    (center radius) #:transparent)
```

Not strictly necessary, but it may make things a bit more clean.

Next, we want a method that can test if a point is in a circle or not:

```scheme
; Test if circle contains a given point
(define (contains? c p)
  (<= (+ (sqr (- (point-x (circle-center c)) (point-x p)))
         (sqr (- (point-y (circle-center c)) (point-y p))))
      (sqr (circle-radius c))))
```

It's straight forward enough. About the most interesting part is that we're squaring the radius rather than taking the square root of the distance. It's just a bit quicker and as easy to think about, so we might as well.

With that, it's easy to write a function that can compare an entire list, stopping as soon as we find any circle that matches:

```scheme
; Check if any circle in a given list cs contains a point (x y)
(define (any-contains? cs p)
  (ormap (λ (c) (contains? c p)) cs))
```

Next, we need to be able to generate random points. First, here's a function that can generate any real number in the range [min, max) (so inclusive and exclusive, respectively):

```scheme
; Return a given number chosen uniformly from [min, max)
(define (rand-range min max)
  (+ min (* (random) (- max min))))
```

And that's all we need to really crack the program. We'll have three basic parts:

```scheme
; Calculate the area of a given circle
(define (area-of circles #:samples [samples 1e6])
  ; Find the range of the circles
  ...

  ; Count how many random darts hit any circle
  ...

  ; Use that ratio to calculate the area of the circles
  ...)
```

The range is straight forward enough, but we need it to make sure we can choose random points that will cover the entire set of circles. There are a few ways to do it, but I'm going to go with `for/fold`. We'll start with infinities on either end, and then take each new edge point in turn if it's smaller/larger.

```scheme
; Find the range of the circles
(define-values (x-min x-max y-min y-max)
  (for/fold ([x-min +inf.0] [x-max -inf.0] [y-min +inf.0] [y-max -inf.0])
    ([c (in-list circles)])
    (values (min x-min (- (point-x (circle-center c)) (circle-radius c)))
            (max x-max (+ (point-x (circle-center c)) (circle-radius c)))
            (min y-min (- (point-y (circle-center c)) (circle-radius c)))
            (max y-max (+ (point-y (circle-center c)) (circle-radius c))))))
```

Next, throw a whole bunch of 'darts' at the circles. Check each, using the `any-contains?` function we defined above. 

```scheme
; Count how many random darts hit any circle
(define hits
  (for/sum ([i (in-range samples)])
    (define dart 
      (point (rand-range x-max x-min)
             (rand-range y-max y-min)))
    (if (any-contains? circles dart) 1 0)))
```

And that's it. The ratio of hits to total samples is the same as the ratio between area within the circles versus the entire rectangle. Multiply out... and we're good to go.

```scheme
; Use that ratio to calculate the area of the circles
(* (/ hits samples)
   (* (- x-max x-min)
      (- y-max y-min)))
```

Putting each of those where they go above (or you can see the entire code <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/overlapping-circles.rkt">here</a>) and we're good to go:

```scheme
> (area-of (list (circle (point 0 0) 1)))
3.142516
> (area-of (list (circle (point -0.5 0) 1) (circle (point  0.5 0) 1)))
5.053098
```

We'll go ahead and run those (along with a few others) using the `test` module and {{< doc racket "rackunit" >}}:

```scheme
(module+ test
  (require rackunit)

  (check-=
   (area-of (list (circle (point 0 0) 1)))
   pi
   0.1
   "Unit circle")

  (check-=
   (area-of (list (circle (point 0 0) 10)))
   (* pi 10 10)
   1
   "Big circle")

  (check-=
   (area-of (list (circle (point 0 0) 0.1)))
   (* pi 0.1 0.1)
   0.01
   "Small circle")

  (check-=
   (area-of (list (circle (point 3 4) 1)))
   pi
   0.1
   "Offset circle")

  (check-=
   (area-of (list (circle (point 0 0) 1)
                  (circle (point 0 0) 0.5)))
   pi
   0.1
   "Smaller circle completely enclosed")

  (check-=
   (area-of (list (circle (point -2 0) 1)
                  (circle (point  2 0) 1)))
   (* 2 pi)
   0.1
   "Two distinct circles")

  (check-=
   (area-of (list (circle (point -0.5 0) 1)
                  (circle (point  0.5 0) 1)))
   5.0548
   0.1
   "Overlapping circles"))
```

Run it... and all good. Every one in a while, you might get some errors (due to the random nature of the tests), but it should be extremely rare. 

That's it. If you'd like to see the entire codebase, you can do so here: <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/overlapping-circles.rkt">overlapping-circles.rkt</a>

---
title: "AoC 2018 Day 6: Infinite Area Simulator"
date: 2018-12-06
programming/languages:
- Racket
programming/sources:
- Advent of Code
series:
- Advent of Code 2018
---
### Source: [Chronal Coordinates](https://adventofcode.com/2018/day/6)

> **Part 1:** Given a list of points, calculate the region of points closest to each point (using {{< wikipedia "Manhattan distance" >}}). Return the size of the largest non-infinite region.

<!--more-->

First, some boilerplate. We want a function to load in the points and then find the bounds of the entire region (we'll need it later):

```racket
; Read constant POINTS for the current input
(define (read-points [in (current-input-port)])
  (for/list ([line (in-lines in)])
    (match-define (regexp #px"(\\d+), (\\d+)" (list _ raw-x raw-y)) line)
    (define x (string->number raw-x))
    (define y (string->number raw-y))
    (point x y)))

(define POINTS (read-points))

; Determine the bounds for the given points
(define-values (MIN-X MAX-X MIN-Y MAX-Y)
  (for/fold ([min-x +inf.0] [max-x -inf.0] [min-y +inf.0] [max-y -inf.0])
            ([pt (in-list POINTS)])
    (values (min min-x (point-x pt))
            (max max-y (point-x pt))
            (min min-x (point-y pt))
            (max max-y (point-y pt)))))

; If a region has more points than are contained in the bounds, it's infinite
(define VOLUME (* (- MAX-X MIN-X) (- MAX-Y MIN-Y)))
```

Next, define our distance function, a function to find the closet point from our list of given points, and a helper that will give the four neighbors to a given point (we'll use this to {{< wikipedia "flood fill" >}}).

```racket
; Manhattan distance
(define (distance p1 p2)
  (+ (abs (- (point-x p1) (point-x p2)))
     (abs (- (point-y p1) (point-y p2)))))

; Return the point in pts closest to the given point pt
(define (closest target)
  (define-values (min-point min-distance)
    (for*/fold ([min-point #f] [min-distance +inf.0])
               ([pt (in-list POINTS)]
                [d (in-value (distance target pt))]
                #:when (<= d min-distance))
      (values (if (= d min-distance) #f pt) d)))
  min-point)

; The four neighbors of a given point
(define (neighbors target)
  (match-define (point x y) target)
  (list (point x (- y 1))
        (point (+ x 1) y)
        (point x (+ y 1))
        (point (- x 1) y)))
```

And that's the bulk of what's needed. With that, we can start on a point and flood fill outwards until we either know we have an infinite area or until we find the boundary of all points that are now as close or closer to a different point:

```racket

; Calculate the number of points closest to this point than any other via floodfill
(define (area target)
  (let loop ([area 0]
             [to-check (list target)]
             [checked (set)])
    (cond
      [(null? to-check) area]
      [else
       (match-define (list-rest current-to-check next-to-check) to-check)
       (define next-checked (set-add checked current-to-check))
       (cond
         ; Already checked this point, ignore
         [(set-member? checked current-to-check)
          (loop area next-to-check checked)]
         ; More than the maximum area, has gone infinite
         [(> area VOLUME)
          +inf.0]
         ; Closest to target, add and expand
         [(equal? target (closest current-to-check))
          (loop (add1 area)
                (append (neighbors current-to-check) next-to-check)
                next-checked)]
         ; Not closest, don't add or expand
         [else
          (loop area next-to-check next-checked)])])))
```

The trick to this algorithm is knowing that no single region will end up bigger than the volume enclosing all of the points. So if the area we're looking at is that big, it will clearly become infinite. While this isn't the best algorithm (we could probably trim down the bounds somewhat), it's still fairly fast. And it lets us finish part 1:

```racket
; Find the largest non-infinite area
(printf "[part1]\n")
(for/fold ([max-point #f] [max-area -inf.0])
          ([pt (in-list POINTS)])
  (define a (area pt))
  (cond
    [(and (not (infinite? a))
          (> a max-area))
     (values pt a)]
    [else
     (values max-point max-area)]))
```

> **Part 2:** Define a new region such that a point {{< inline-latex "p_1" >}} is in the region if the sum of distances to all input points is less than a given number {{< inline-latex "R" >}}.

This one took a bit to wrap my head around what they were asking. In the end though, the code ends up being a fairly direct translation of the problem statement. We keep a set of points to check, then move them over as we check them, adding them to the `region` if they satisfy the given condition.

```racket
; Find the center point and flood fill out to all points with X of all points
(define (points-within-range range)
  (let loop ([to-check (set (point (exact-round (/ (+ MIN-X MAX-X) 2))
                                   (exact-round (/ (+ MIN-X MAX-X) 2))))]
             [checked (set)]
             [region (set)])
    (cond
      ; Base case: checked all points, return region
      [(set-empty? to-check) region]

      ; Already checked this point, ignore
      [(set-member? checked (set-first to-check))
       (loop (set-rest to-check) checked region)]

      ; Sum of distances is less than range, include and expand search
      [(< (for/sum ([pt (in-list POINTS)])
            (distance (set-first to-check) pt))
          range)
       (loop (set-union (for/set ([neighbor (in-list (neighbors (set-first to-check)))]
                                  #:when (not (set-member? checked neighbor)))
                          neighbor)
                        (set-rest to-check))
             (set-add checked (set-first to-check))
             (set-add region (set-first to-check)))]

      ; Not in region, skip
      [else
       (loop (set-rest to-check) (set-add checked (set-first to-check)) region)])))
```

The most interesting case is the third one, mostly because of a few optimizations to make the code a bit quicker. First, we sum up distances and use that to determine if the sum of distances is within range (have I mentioned how much I like the {{< doc racket for >}}) family of macros)[^yes]?

Print it out and you're done:

```bash
$ cat input.txt | racket infinite-area-simulator.rkt

[part1]
(point 241 157)
3882

[part2]
43852 are within 10000
```

{{< figure src="/embeds/2018/joliver-cool.gif" >}}

As an added bonus, while I was working out how to generate an image for the regions produced by part 1:

```racket
(define color-for
  (let ([colors (for/list ([pt (in-list POINTS)]) (vector (random) (random) (random)))])
    (λ (pt)
      (define closest-pt (closest pt))
      (or
       (for/first ([color (in-list colors)]
                   [pt^ (in-list POINTS)]
                   #:when (equal? closest-pt pt^))
         color)
       (vector 0 0 0)))))

(define (write-image-debug filename)
  (send
   (flomap->bitmap
    (build-flomap*
     3 (exact-round (- MAX-X MIN-X)) (exact-round (- MAX-Y MIN-Y))
     (λ (x y) (color-for (point (+ x MIN-X) (+ y MIN-Y))))))
   save-file
   filename
   'png))
```

{{< figure src="/embeds/2018/aoc-6-regions.png" >}}

The colors are random each time you run the program, but it's still pretty neat to do.

[^yes]: {{< figure src="/embeds/2018/tennant-oh-yes.gif" >}}

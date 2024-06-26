---
title: Triangle Trilemma
date: 2013-01-20 14:00:55
programming/languages:
- Racket
- Scheme
programming/sources:
- Programming Praxis
programming/topics:
- Geometry
- Mathematics
- Trigonometry
---
[Four points, a square?]({{< ref "2013-01-03-four-points-a-square.md" >}})) and comes originally from a <a title="Google Code Jam: Triangle Trilemma" href="https://code.google.com/codejam/contest/32014/dashboard">Google Code Jam</a> problem. The problem is stated simply enough

> Accept three points as input, determine if they form a triangle, and, if they do, classify it at equilateral (all three sides the same), isoceles (two sides the same, the other different), or scalene (all three sides different), and also classify it as acute (all three angles less than 90 degrees), obtuse (one angle greater than 90 degrees) or right (one angle equal 90 degrees).

But once you start implementing it, that's when things get more interesting. :smile:

<!--more-->

To start with, I'm going to define a `point` structure:

```scheme
(define-struct point (x y) #:transparent)
```

This will give us `make-point`, `point-x`, and `point-y`, each of which should save somewhat on sanity as opposed to just directly using lists or some such.

With that, we can write two functions that are going to be rather helpful to us later (if you'd like to follow along, you can download the source <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/triangles.rkt" title="Triangles source on GitHub">here</a>).

First, a straight forward distance function, using the aforementioned point structure:

```scheme
; distance between two points
(define (dist p1 p2)
  (sqrt (+ (sqr (- (point-x p1) (point-x p2)))
           (sqr (- (point-y p1) (point-y p2))))))
```

Next (and more importantly), we write the corresponding function for angles. This works because we have all three sides of a triangle, thus we can use the side-side-side equations from trig to calculate any of the angles. To keep things sane, we will return the angle around the middle of the three points.

```scheme
; calculate the angle at B from three points A, B, C
;     B
; ab / \ bc
;   A---C
;     ac
(define (angle a b c)
  (define ab (dist a b))
  (define bc (dist b c))
  (define ac (dist a c))
  (cond
    [(= (* 2 bc ac) 0)
     0]
    [else
     (clamp (acos (/ (+ (sqr bc) (sqr ac) (- (sqr ab)))
                     (* 2 bc ac)))
            pi)]))
```

You can see the `clamp` function if you check out the <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/triangles.rkt" title="Triangles source on GitHub">full source</a>. Basically, it does modular arithmetic on floating point numbers, forcing them into a given range. 

Next, we're going to write that actual classification function. Starting with the three points, we'll calculate the distances and angles. This is one of the (admittedly silly) reasons that I love Schemes. You can use just about anything for identifiers!

```scheme
; classify a triangle
; return equilateral/isosceles/scalene and acute/obtuse/right
;     B
; ab / \ bc
;   A---C
;     ac
(define (classify a b c)
  ; get sides
  (define ab (dist a b))
  (define bc (dist b c))
  (define ac (dist a c))
  (define dists (sort (list ab bc ac) >))

  ; get angles
  (define /_a (angle c a b))
  (define /_b (angle a b c))
  (define /_c (angle b c a))
  (define angles (sort (list /_a /_b /_c) >))

  ...)
```

After we have that, there are a series of sanity checks that we have to run. These are all that I could think of and seem to be working, but if I missed anything, be sure to let me know (preferably with a failing test case).

```scheme
; sanity check
(cond
  ; not a triangle
  [(or 
    ; angles must add up
    (not (=ish (apply + angles) pi))
    ; triangle inequality
    (or (>ish (car dists) (+ (cadr dists) (caddr dists)))
        (=ish (car dists) (+ (cadr dists) (caddr dists))))
    ; zero angles
    (or (=ish /_a 0)
        (=ish /_b 0)
        (=ish /_c 0)))
   #f]

  ...)
```

Here we're using the `>ish` and `=ish` functions which basically add a tolerance to deal with floating point rounding issues (which were throwing off a few of the tests). You can see them as well in the <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/triangles.rkt" title="Triangles source on GitHub">full source</a>. 

Once we have that, it's time to classify. First, we'll classify the sides:

```scheme
; equilateral/isosceles/scalene
(cond
  [(=ish ab bc ac)
   'equilateral]
  [(or (=ish ab bc)
       (=ish ab ac)
       (=ish bc ac))
   'isosceles]
  [else
   'scalene])
```

Then the angles:

```scheme
; acute/obtuse/right
(cond
  [(>ish (car angles) RIGHT-ANGLE)
   'obtuse]
  [(=ish (car angles) RIGHT-ANGLE)
   'right]
  [else
   'acute])
```

`RIGHT-ANGLE` is defined as `(/ pi 2)`. I accidentally had it as `(/ pi 4)` at first... Took took longer than I care to admit to debug.

And that's it. Return those two as a list and you're good to go. The Google Jam had a series of test cases which I converted to Racket Unit Test:

```scheme
; whee testing!
; source: https://code.google.com/codejam/contest/32014/dashboard
(for ([pts (in-list '((0 0 0 4 1 2)
                      (1 1 1 4 3 2)
                      (2 2 2 4 4 3)
                      (3 3 3 4 5 3)
                      (4 4 4 5 5 6)
                      (5 5 5 6 6 5)
                      (6 6 6 7 6 8)
                      (7 7 7 7 7 7)))]
      [ans (in-list '((isosceles obtuse)
                      (scalene acute)
                      (isosceles acute)
                      (scalene right)
                      (scalene obtuse)
                      (isosceles right)
                      #f
                      #f))])
  (check-equal?
   (classify (make-point (list-ref pts 0) (list-ref pts 1))
             (make-point (list-ref pts 2) (list-ref pts 3))
             (make-point (list-ref pts 4) (list-ref pts 5)))
   ans))
```

All of those ran without complaint, so for the time being I think we have a winner. I should check if there are any strange cases (like there were with the squares), but I haven't found one yet. I'll keep watching the comments here and on Programming Praxis to see if anyone posts one though.

If you'd like to see the entire source and haven't already clicked on one of the other links, you can do so here:
- <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/triangles.rkt" title="Triangles source on GitHub">Triangles source</a>

---
title: Four points, a square?
date: 2013-01-03 14:00:45
programming/languages:
- Racket
- Scheme
programming/sources:
- Programming Praxis
programming/topics:
- Geometry
- Mathematics
---
<a title="Four Points Determine a Square" href="http://programmingpraxis.com/2013/01/02/four-points-determine-a-square/">Another post</a> from Programming Praxis. This one was originally intended for Friday but they posted it early, so I figured I would go ahead and do the same. The problem is actually deceptively straight forward:

Given four points, do they form a square?

<!--more-->

My first thought was to directly calculate the angles between each trio of points. You should be able to determine which trios are ordered by finding the 90 degree angles and you could then check the distances. Before I got too far into my old geometry textbooks to figure out how to calculate those angles though, I realized that you'd don't actually need the angles at all.

Instead, all you need is three distances. If you calculate the distances from one point to the other three, a square will always have two equal and short distances on the sides and another multiple of the square root of two across the diagonal. Better yet, only squares have those three distances. So just start at any one point and run these calculations:

```scheme
; test if four points for a square
(define (square? pts)
  ; calculate and sort the pairwise distances
  (define dists
    (sort
     (list (dist (car pts) (cadr pts))
           (dist (car pts) (caddr pts))
           (dist (car pts) (cadddr pts)))
     <))

  ; two must be equal, those are edges
  ; the last is the diagonal and should be sqrt 2 * edge
  (and (= (car dists)
          (cadr dists))
       (= (caddr dists)
          (* (sqrt 2) (car dists)))))
```

This is assuming that you have `sqr` and `dist` defined as such:

```scheme
; square a number
(define (sqr x) (* x x))

; standard distance function
(define (dist p1 p2)
  (sqrt (+ (sqr (- (cadr p2) (cadr p1)))
           (sqr (- (car p2) (car p1))))))
```

To test it out, we'll run all of the tests provided in the original post from Programming Praxis:

```scheme
>(square? '((0 0) (0 1) (1 0) (1 1))) ; unit square
#t
>(square? '((0 0) (2 1) (3 -1) (1 -2))) ; at an angle
#t
>(square? '((0 0) (1 1) (0 1) (1 0))) ; re-ordered points
#t
>(square? '((0 0) (0 2) (3 2) (3 0))) ; rectangle
#f
>(square? '((0 0) (3 4) (8 4) (5 0))) ; rhombus
#f
>(square? '((0 0) (0 0) (1 1) (0 0))) ; not a polygon
#f
>(square? '((0 0) (0 0) (1 0) (0 1))) ; not a polygon
#f
```

Looks good to go. It's interesting how something like that can actually be pretty simple. Just three distance calculations and you're golden.

Except, it turns out that it's not quite so simple. This actually ended up being the same idea as the <a href="http://programmingpraxis.com/2013/01/02/four-points-determine-a-square/2/" title="Solution for Four Points Determine a Square">original solution</a> provided at Programming Praxis, but as another commenter pointed out (<a href="http://bonsaicode.wordpress.com/2013/01/02/programming-praxis-four-points-determine-a-square/" title="Programming Praxis - Four Points Determine a Square">their solution in Haskell</a>), there's one test case that this method fails on:

```scheme
> (square? '((0 0) (0 1) (1 0) (-1 -1))) ; designed to fail
#f
```

In this case, the distances are all correct (you have two sides and a square root of 2 multiple for the diagonal) but unfortunately the diagonal goes the wrong direction. So how do you fix that case?

Well, you should just be able to test the sides from the far point. That requires figuring out which distance that belonged to though (which isn't horrible), but I wanted something a bit more amusing. So what I've done here is extend the function out to calculate all 16 pairwise distances between the points (including self comparisons):

```scheme
; calculate all pairwise distances
(define dists
  (sort
   (for*/list ([a (in-list pts)]
               [b (in-list pts)])
     (dist a b))
   <))
```

What we should get is four zeros (for the self comparisons), eight copies of the sides (because order isn't preserved we have both the side *ab* and *ba* for each side), and four copies of the diagonal at a square root of two multiple. Using `take` and `drop` on a sorted list to pull out those sections and making sure they are equal (it's times like these that I remember and am glad that `=` takes two *or more* arguments), and everything should work out nicely:

```scheme
; we should have:
(and
 ; 4x zero for self matches
 (apply = (cons 0 (take dists 4)))
 ; 8x identical distances for the sides
 (apply = (take (drop dists 4) 8))
 ; 4x sqrt(2) * side for the diagonals
 (apply = (cons (* (sqrt 2) (car (drop dists 4)))
                (drop dists 12))))
```

It's a bit strange and definitely not the most efficient (`take` and `drop` are duplicating work and I believe that `apply` isn't necessarily the most efficient thing, although I could be wrong), but for the number of tests we're doing, it's still essentially instantanous.

This time, I also added a series of {{< doc racket "RackUnit" >}} tests to make sure everything works:

```scheme
(check-true (square? '((0 0) (0 1) (1 0) (1 1))) "unit square")
(check-true (square? '((0 0) (2 1) (3 -1) (1 -2))) "at an angle")
(check-true (square? '((0 0) (1 1) (0 1) (1 0))) "re-ordered points")

(check-false (square? '((0 0) (0 2) (3 2) (3 0))) "rectangle")
(check-false (square? '((0 0) (3 4) (8 4) (5 0))) "rhombus")
(check-false (square? '((0 0) (0 0) (1 1) (0 0))) "not a polygon")
(check-false (square? '((0 0) (0 0) (1 0) (0 1))) "not a polygon")

(check-false (square? '((0 0) (0 1) (1 0) (-1 -1))) "failed original test")
```

Running it, there are no errors, so everything appears to be good. Hopefully there isn't another sneaky sort of error going on, but for the moment I doubt it.

As mentioned, this is the sort of thing that you may see on those puzzle sort of interview questions. While I don't personally think there's much worth in that sort of question (more often than not, you're testing if someone has heard the question before), they're still often fun to work out the first time. I'd be particularly interested to see how an interviewer would deal with the first (incorrect) solution and how the interviewee could deal with being told that there's a corner case that they missed but not which one.

If you'd like to see the entire source code for this post, you can do so here:

- <a title="Four points a square source on GitHub" href="https://github.com/jpverkamp/small-projects/blob/master/blog/four-points-a-square.rkt">four-points-a-square.rkt</a>

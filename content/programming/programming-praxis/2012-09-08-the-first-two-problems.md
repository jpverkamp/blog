---
title: The First Two Problems
date: 2012-09-08 14:00:09
programming/languages:
- Scheme
programming/sources:
- Programming Praxis
---
Anything worth doing is worth over doing, right? This time we have another two problems from Programming Praxis, aptly title "[Turtle Graphics]({{< ref "2012-04-13-wombat-ide-turtle-graphics.md" >}}) instead of just printing the characters. :smile:

<!--more-->

As always if you would like to download the entire source code, you can do so [here](https://github.com/jpverkamp/small-projects/blob/master/blog/first-two-problems.ss). Granted, you'll almost surely need [source code](https://github.com/jpverkamp/small-projects/blob/master/blog/first-two-problems.ss).

Now the big question is how do you actually draw those? It turns out, it's not so bad. Here's the first function which takes a vector of point lists (like `digits` above) and draws the list at a given point with the given turtle:

```scheme
; using turtle t, draw the digit/letter with index i from table chars
; with the top left at r, c
; reset the turtle to wherever it was after that
(define (draw-thing chars t r c i)
  (block t
    (let ([ps (vector-ref chars i)])
      (lift-pen! t)
      (move-to! t (+ c (cadar ps)) (+ r (caar ps)))
      (drop-pen! t)
      (let loop ([ps (cdr ps)])
        (unless (null? ps)
          (move-to! t (+ c (cadar ps)) (+ r (caar ps)))
          (loop (cdr ps)))))))
```

Pretty straight forward. Save the state, lift the pen to move to the first point, and then recursively draw lines from point to point. Now what if we want to use that to draw a number? Still pretty straight forward. Just loop through the digits, drawing them one at a time. The hardest part was actually formatting them from the right so that the standard `mod`/`div` method for extracting digits would work.

```scheme
; using turtle t, draw a number n with the top left at r, c
; reset the turtle to whever it was after that
(define (draw-number t r c n)
  (block t
    (if (= n 0)
        (draw-thing digits t r (+ c 10) 0)
        (let ([? (< n 0)])
          (let loop ([c (+ c (* 10 (digits-in n)) 1)]
                     [n (abs n)])
            (when (> n 0)
              (draw-thing digits t r c (mod n 10))
              (loop (- c 10) (div n 10)))
            (when (and ? (= n 0))
              (draw-thing digits t r c 10)))))))
```

In case you were wondering, here's the function that will tell me how many characters are in a number, including an extra one for the `-` in negative numbers:

```scheme
; helper to calculate how wide a number is (add one for negative numbers)
(define (digits-in n)
  (if (= n 0) 
      0
      (+ (if (< n 0) 1 0)
        (inexact->exact (+ 1 (floor (log (abs n) 10)))))))
```

After getting numbers working, drawing strings was much easier. Particularly because you can directly access the letters from left to right with `string-ref`:

```scheme
; using turtle t, draw a string s with the top left at r, c
; reset the turtle to whever it was after that
(define (draw-string t r c s)
  (block t
    (for-each
      (lambda (i)
        (unless (eq? #\space (string-ref s i))
          (draw-thing letters t r (+ c (* i 10))
            (- (char->integer (char-upcase (string-ref s i))) 65))))
      (iota (string-length s)))))
```

And that's it. Well, except for the minor fact that we haven't actually solved the problem yet. :smile:

```scheme
; draw a temperature table
; (draw-image (make-temperature-table))
(define (make-temperature-table)
  (let ([t (hatch)])
    (draw-string t 15 0 " F")
    (draw-string t 15 50 " C")
    (for-each
      (lambda (row)
        (let* ([f (* row 20)]
               [c (inexact->exact (round (/ (* (- f 32) 5) 9)))])
          (draw-number t (* (- row) 15) 0 f)
          (draw-number t (* (- row) 15) 50 c)))
      (iota 16))
    (turtle->image t)))

; draw hello world
; (draw-image (hello-world))
(define (hello-world)
  (let ([t (hatch)])
    (draw-string t 0 0 "Hello World")
    (turtle->image t)))
```

Much better.

That was actually really fun to do. Perhaps I'll see what other ~~trouble~~ fun I can get into with it. 

If you would like to download the entire source code, you can do so [Turtle Graphics]({{< ref "2012-04-13-wombat-ide-turtle-graphics.md" >}})). 

As a random side note, it's amusing to watch the turtles actually going about the drawing. Try turning on `(live-display #t)`.

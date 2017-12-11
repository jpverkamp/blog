---
title: Knight moves
date: 2013-03-11 22:00:20
programming/languages:
- Racket
- Scheme
programming/sources:
- Programming Praxis
programming/topics:
- Chess
---
How many ways are there for a knight in chess from the top left to the bottom right of a chess board in exactly *n=6* moves?

<!--more-->

Well, that's exactly the problem stated in the most recent <a title="Knight Moves" href="http://programmingpraxis.com/2013/03/08/knight-moves/">Programming Praxis post</a> from Friday. The goal is to generalize to any path length, but the general solution is actually somewhat easier to write.

The general idea for this problem is to think recursively. You have three variables that you need to contend with: the *source* square you are moving from (which will change at each step of the recursion), the *destination* square you are eventually moving to (which will not), and the *number of moves* you have left to reach it. If, at each step, you can calculate all of the possible next moves, you can recur on the number of remaining moves. Let the base case be when the *number of moves *reaches zero (and *source* may or may not equal *destination*). So we're looking at something like this:

```scheme
; find all paths from src to dst in exactly the given moves
(define (knight-moves src dst moves)
  (cond
    ; if we're out of moves, check if we've found a solution
    ; either return just the destination or the empty list
    [(= moves 0)
     (if (equal? src dst) (list dst) '())]
    ; otherwise, step in all 8 possible directions
    ; only keep solutions that stay on the board
    [else
     (for/list ([nxt (in-list (knight-neighbors src))]
                #:when (in-bounds? nxt) 
                [recur (in-list (knight-moves nxt dst (- moves 1)))])
       (cons src recur))]))
```

The advantage here is that we can use the *for* with a *#:when *to loop over the possible knight moves, but only include the ones that stay on the board. Also, dividing the two conditions by a *#:when* essentially makes the *for* act like a *for**, making the loop nested. That way we will automatically take out paths that do not end with a valid solution, since they will not take part in the inner loop.

To get this working though, we need a function that will return the neighbors (so far as a knight is concerned) for a given point:

```scheme
; return the eight neighboring points for a knight
; a for loop without for* will loop in sync across the lists
(define (knight-neighbors pt)
  (for/list ([xd (in-list '(-2 -2 -1 -1  1  1  2  2))]
             [yd (in-list '(-1  1 -2  2 -2  2 -1  1))])
    (make-point (+ (point-x pt) xd)
                (+ (point-y pt) yd))))
```

This time, we're using the *for* loop without the nesting, so that the two iteration variables (*xd* and *yd*) are kept in sync.

And that's basically all that we need. Technically, I haven't included the code for *in-bounds?* or the structure definition, but both of those are rather straight forward. You can see the <a title="Knight moves source" href="https://github.com/jpverkamp/small-projects/blob/master/blog/knight-moves.rkt">full source on GitHub</a>.

In answer to the original question:

```scheme
> (length (knight-moves (make-point 0 0)
                        (make-point 7 7)
                        6))
108
```

So there are exactly 108 ways that you can get a knight from the top left to the bottom right (or top right to bottom left I guess) of a chess board in exactly six moves. It takes about 15 ms to calculate that too, so none too shabby. I'm sure that if we were looking at a larger, more generic version of the problem (say any *m* x *n* board or generating paths that are any longer), then a dynamic solution which would cache subpaths might be helpful, but for the standard chess board size and *&le;6*, it's not necessary. Perhaps another day.
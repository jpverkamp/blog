---
title: 'Chess Puzzles: Knight''s Tour'
date: 2014-09-04 20:00:00
programming/languages:
- Racket
- Scheme
programming/topics:
- Backtracking
- Chess
- Heuristics
series:
- Chess Puzzles
---
Onwards and upwards! For today's chess puzzle, let's take a first crack at the [[wiki:Knight's Tour]]()[^1]

{{< figure src="/embeds/2014/tour-5-solution.gif" >}}

<!--more-->

As with [N Queens]({{< ref "2014-09-03-chess-puzzles-n-queens.md" >}}), the problem is simply stated:

> A knight's tour is a sequence of moves of a knight on a chessboard such that the knight visits every square only once.

And once again, we can get a solution working relatively well using [[wiki:backtracking]]():

```scheme
(define-piece Knight (move 1 (leaper 1 2)))
(define-piece Visited '())

; Solve a knights tour on a given board
(define (knights-tour width [height width])
  ; Create a new empty board
  (define b (make-board width height #:pieces (list Knight Visited)))

  ; A board is completed if there are no empty squares
  ; All squares are either the Knight or Visited
  (define (completed? b)
    (not (for*/first ([x (in-range width)]
                      [y (in-range height)]
                      #:when (not (board-ref b (pt x y))))
           #t)))

  ; Move the knight from the given point to each possible next point in turn
  ; Return a list of valid moves to finish the tour if such a list exists, #f otherwise
  (define (move-knight b p)
    (cond
      ; Done, we have a tour and there are no more valid moves necessary
      [(completed? b) '()]
      ; Otherwise, try all possible moves from this point
      ; Since all pieces are the same color, moves from is only empty tiles
      [else
       (for*/first ([next (in-list (moves-from b p))]
                    [recur (in-value (let* ([b (board-move b p next)]
                                            [b (board-set b p '(Black Visited))])
                                       (move-knight b next)))]
                    #:when recur)
         (cons p recur))]))

  ; Try each possible initial location until we find one that works
  (for*/first ([x (in-range width)]
               [y (in-range height)]
               [solution (in-value
                           (move-knight
                             (board-set b (pt x y) '(Black Knight))
                             (pt x y)))]
               #:when solution)
    solution))
```

Basically, there are three interesting pieces here: `completed?`, `move-knight`, and the `for*/first` initial loop.

First, how can a tour be `completed?` If all of the locations on the board are filled. We get around this with the psuedo-piece: `Visited`. It fills up the board as we continue to move our knight around. Technically, I could have just filled the board with knights, but I like how visited lets us visualize things.

Next, `move-knight`. This is the core of the algorithm. As it states, we are building up a list of moves recursively. So the base case (when the board is completed) return the empty list `'()`. Otherwise, we're going to use {{< doc racket "for*/first" >}} to find the first move which recursively solves the problem (or `#f` if none does). The use of {{< doc racket "in-value" >}} is a trick I picked up <a href="https://groups.google.com/forum/#!topic/racket-users/p2S6F3FAiU0">from the mailing list</a> for using an 'expensive' value in a `#:when` clause and body without having to recalculate it.

Finally, we loop across all of the starting states. It doesn't matter in the case of closed tours (where the start and end points match and thus any point can be a start point), but on some boards not every starting location is valid.

So now we can solve a tour:

```scheme
> (knights-tour 5)
(list
 (pt 0 0) (pt 1 2) (pt 0 4) (pt 2 3) (pt 3 1)
 (pt 1 0) (pt 0 2) (pt 1 4) (pt 2 2) (pt 4 3)
 (pt 2 4) (pt 0 3) (pt 1 1) (pt 3 0) (pt 4 2)
 (pt 3 4) (pt 1 3) (pt 0 1) (pt 2 0) (pt 4 1)
 (pt 3 3) (pt 2 1) (pt 4 0) (pt 3 2))
```

Whee! Okay, what does that actually look like? Let's animate it!

```scheme
(current-glyphs (hash 'Knight "♞"
                      'Visited "♘"))

; Render a knights tour into an animation
(define (knights-tour/animate-solution width [height width])
  (define tour (knights-tour width height)

  ; Create an initial board
  (define board (make-board width height #:pieces (list Knight Visited)))

  ; Prerender the board once so we know how large of a scene to create
  (define r (render board #:player-colors (const "black")))
  (define render-width (send r get-width))
  (define render-height (send r get-height))

  ; Animate the tour, rendering each frame once
  (big-bang tour
    [on-tick cdr]
    [to-draw (λ (tour)
               (place-image
                (render (if (null? tour)
                            board
                            (board-set board (car tour) '(Black Knight))))
                (/ render-width 2)
                (/ render-height 2)
                (empty-scene render-width render-height)))]
    [stop-when null?]
    [record? #t]))
```

```scheme
> (knights-tour/animate-solution 5)
```

{{< figure src="/embeds/2014/tour-5-solution.gif" >}}

Shiny.

Okay, so that's all well and good for normal boards. What if instead you want a board with holes in it / a non-regular board?

Simple! We'll just add a third type of piece `Invalid` and pre-populate the board with those:

```scheme
(current-glyphs (hash 'Knight "♞"
                      'Invalid "✗"
                      'Visited "♘"))

(define-piece Knight (move 1 (leaper 1 2)))
(define-piece Invalid '())
(define-piece Visited '())

; Solve a knights tour on a given board (optionally with some pieces removed)
(define (knights-tour width [height width] #:removed [removed '()])
  ; Create a new board (potentially removing some pieces)
  (define b
    (for/fold ([b (make-board width height
                    #:pieces (list Knight Invalid Visited))])
              ([p (in-list removed)])
      (board-set b p '(Black Invalid))))

  ...)
```

All the rest of the code stays the same. Pretty nice eh? Let's try an example:

```scheme
> (knights-tour/animate-solution 4
    #:removed (list (pt 1 0) (pt 0 2) (pt 0 3) (pt 2 3) (pt 3 3)))
```

{{< figure src="/embeds/2014/tour-4-limited-solution.gif" >}}

Hmm, that's all well and code showing off the final tour. But what if we want to see the search in progress? Let's put in a {{< doc racket "generator" >}} again so we can animate this. This time around though, I'm actually going to fold the generator code into the main method rather than duplicating a bunch of code.

```scheme
(define (knights-tour width [height width] #:generator? [generator? #f])
  (define g
    (generator ()
      ...

      (define (move-knight b p)
        (when generator?
          (yield b p))

        ...)))

  (if generator? g (g)))
```

In this case, we create the `generator` no matter what. But we only call `yield` if we actually specify it to the function. This way we can see each step of our simultion as we go. If we don't want the generator, we immediately call it as we're returning, forcing it to return a value: the implicit `yield` at the end of the function.

So with this, we have enough that we can animate the search space:

```scheme
; Render the search for a knights tour into an animation
(define (knights-tour/animate-search width [height width] #:removed [removed '()])
  ; Create an initial board including the missing tiles
  (define board
    (for/fold ([b (make-board width height #:pieces (list Knight Invalid Visited))])
              ([p (in-list removed)])
      (board-set b p '(Black Invalid))))

  ; Prerender the board once so we know how large of a scene to create
  (define r (render board #:player-colors (const "black")))
  (define render-width (send r get-width))
  (define render-height (send r get-height))

  ; Set the last board, which will be updated on each yield
  (define last-board board)
  (define last-point (pt 0 0))
  (define g (knights-tour width height #:removed removed #:generator? #t))

  ; Animate the tour, rendering each frame once
  ; Stop when the generator returns 1 value
  (big-bang #t
    [on-tick
     (λ (running?)
       (and running?
            (with-handlers ([exn? (const #f)])
              (define-values (board point) (g))
              (set! last-board board)
              (set! last-point point)
              #t)))]
    [to-draw
     (λ (_)
       (place-image
        (render last-board)
        (/ render-width 2)
        (/ render-height 2)
        (empty-scene render-width render-height)))]
    [stop-when (negate identity)]
    [record? #t]))
```

And in action:

```scheme
> (knights-tour/animate-search 4
     #:removed (list (pt 1 0) (pt 0 2) (pt 0 3) (pt 2 3) (pt 3 3)))
```

{{< figure src="/embeds/2014/tour-4-limited-search.gif" >}}

Sweet!

That's about all for today. If you were following along though, you might have noticed one very important omission...

It doesn't work on 8x8 boards.

Well, that's not strictly speaking true. It will work. If you wait long enough, you will eventually get a solution, but it's going to be a *very* long wait. So looks like we'll need a follow looking for a better solution[^2]

That's for another time though. If you'd like to see the entire code, you can do so in the <a href="https://github.com/jpverkamp/chess-puzzles">chess-puzzles</a> repo on GitHub: <a href="https://github.com/jpverkamp/chess-puzzles/blob/master/puzzles/knights-tour.rkt">knights-tour.rkt</a>. Check it out!

[^1]: Backtracking is wicked slow on this one, we're going to have to solve it twice.
[^2]: Perhaps one using [[wiki:neural networks]]()? Been a while since I've worked with those...
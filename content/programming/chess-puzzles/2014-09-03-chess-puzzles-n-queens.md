---
title: 'Chess Puzzles: N Queens'
date: 2014-09-03 20:00:00
programming/languages:
- Racket
- Scheme
programming/topics:
- Backtracking
- Chess
series:
- Chess Puzzles
---
After two weeks, it seems only right that we actually get around to a real chess puzzle. First on the list: [[wiki:the eight queens puzzle|Eight queens puzzle]]().

{{< figure src="/embeds/2014/8-queens-solution.png" >}}

Specifically, how do you place n queens on an n by n chess board such that no pair of queens can attack one another?

<!--more-->

Those of you paying attention may think this problem looks [awfully familiar]({{< ref "2012-09-24-n-queens-in-18-lines-of-code.md" >}}). Turns out I've already done this one. But not with my new [chess library]({{< ref "2013-02-01-1gam-chesslike-1-0-did-it.md" >}})! So let's do it again:

Basically, the idea is simple. Start in the first row and column, placing a queen:

{{< figure src="/embeds/2014/8-queens-step-1.png" >}}

Next, move down to the second row, first column:

{{< figure src="/embeds/2014/8-queens-step-2.png" >}}
{{< figure src="/embeds/2014/8-queens-step-3.png" >}}
{{< figure src="/embeds/2014/8-queens-step-4.png" >}}

We cannot place a queen there since it can attack the first. Try the second column ... Still doesn't work, since it can attack diagonally. Try the third... Bam. Placed. Head down to the third row and start over in the first column.

{{< figure src="/embeds/2014/8-queens-step-5.png" >}}

Keep on keeping on. Eventually though, you'll run into a row when you can't place a queen. What do you do then?

[[wiki:Backtrack!|Backtracking]]()

Specifically, go back one row and remove that queen. Start over from one column to the right of where it was. If there's no where else to place that queen, back up another column, over and over until you finally find where you can place one.

Sounds crazy, keeping track of all that state (how many queens we've removed and which), but this is where the magic of recursion comes in. We can actually use the call stack to handle all of this backtracking for us!

```scheme
; Try to place n queens on an nxn chessboard such that none are threatened
(define (queens n)
  ; Create a new nxn board
  (current-board-size n)
  (define-piece Queen (move 'n '*))
  (define b (make-board n #:pieces (hash 'Queen Queen)))

  ; Try to place a queen in each row
  (let place-queen ([board b] [x 0] [y 0])
    (cond
      ; Done with all of the rows, we have a valid configuration
      [(>= y n) board]
      ; Done with the current row, if we haven't placed a queen yet, bail out
      [(>= x n) #f]
      ; Otherwise, try to place the queen at this location
      ; Use the row as the player ID so they can all attack one another
      [else
       (define new-board (board-set board (pt x y) `(,y Queen)))
       (cond
         ; We attack a current queen, try the next square on the old board
         [(for/first ([target-pt (moves-from new-board (pt x y))]
                      #:when (board-ref new-board target-pt))
            #t)
          (place-queen board (+ x 1) y)]
         ; We do not attack anything (yet), try this solution
         ; If that fails, fall through (or short circuits)
         [else
          (or (place-queen new-board 0 (+ y 1))
              (place-queen board     (+ x 1) y))])])))
```

The interesting parts of the solution are at the beginning (when we set up the intial board using our new library) and the {{< doc racket "for/first" >}} section. That's what's checking out attacks. In this case, `for/first` will return `#t` if any `#:when` is true, `#f` if none of them are. This works with our framework (as the code mentions) because we're setting each queen to a different player so they can all attack one another.

```scheme
> (render (queens 8))
```

{{< figure src="/embeds/2014/8-queens-solution.png" >}}

Nice!

Even bigger?

```scheme
> (render (queens 13))
```

{{< figure src="/embeds/2014/13-queens.png" >}}

```scheme
> (render (queens 25) #:tile-size 12)
```

{{< figure src="/embeds/2014/25-queens.png" >}}

(That one took a little while.)

Okay, so that's all well and good. But what if we don't want just one solution. What if we want all of them? Well, it turns out, that's actually not that much harder. We just need to slightly tweak how we recur. Instead of a board or `#f`, we need to return a list of possible solutions. That way we can `append` instead of `or`:

```scheme
; Try to place n queens on an nxn chessboard such that none are threatened
(define (queens n #:all? [generate-all? #f])
  ...

      ; Done with all of the rows, we have a valid configuration
      [(>= y n) (if generate-all? (list board) board)]
      ; Done with the current row, if we haven't placed a queen yet, bail out
      [(>= x n) (if generate-all? (list)       #f)]

      ...

         ; We do not attack anything (yet), try this solution
         ; If that fails, fall through (or short circuits)
         ; If we're generating all solutions, do both
         ; (we cannot do ((if generate-all? append or) ...) because or is a macro
         [generate-all?
          (append (place-queen new-board 0 (+ y 1))
                  (place-queen board     (+ x 1) y))]

         ...)
```

That way, we could get all of the 6x6 solutions in one go:

```scheme
> (map (λ (b) (render b #:player-colors (const "black")))
       (queens 6 #:all? #t))
```

{{< figure src="/embeds/2014/6-queens-1.png" >}} {{< figure src="/embeds/2014/6-queens-2.png" >}} {{< figure src="/embeds/2014/6-queens-3.png" >}} {{< figure src="/embeds/2014/6-queens-4.png" >}}

Or determine how many queens that there are for each puzzle size:

```scheme
> (for/list ([n (in-range 1 11)])
    (list n (length (queens n #:all? #t))))
'((1 1) (2 0) (3 0) (4 2) (5 10) (6 4) (7 40) (8 92) (9 352) (10 724))
```

That matches up perfectly with sequence <a href="https://oeis.org/A000170">A000170</a> on [[wiki:OEIS]](), which must mean we're doing something right. Shiny!

One final trick, what if we want to animate these things? Well, for that we're going to use the {{< doc racket "racket/generator" >}} module. I've used it before, and although the performance isn't *great*, it's certainly the easiest way to get what we want. Really, we only need two changes:

```scheme
; Try to place n queens on an nxn chessboard such that none are threatened
(require racket/generator)
(define (queens-generator n #:all? [generate-all? #f])
  (generator ()
    ...

    ; Try to place a queen in each row
    (let place-queen ([board b] [x 0] [y 0])
      (yield board x y)
      (cond
        ...
```

That way, if we create a generator and keep calling it, it will return each board state including the backtracking. It's a little more complicated to turn it into a nice animation, once again using the excellent {{< doc racket "big-bang" >}} function:

```scheme
; Use the queens generator to render an n-queens problem
(require 2htdp/image 2htdp/universe)
(define (queens-animate n #:all? [generate-all? #f])
  (define g (queens-generator n #:all? generate-all?))

  (define-values (last-board last-x last-y) (g))
  (define done? #f)

  (define r (render last-board #:player-colors (const "black")))
  (define w (send r get-width))
  (define h (send r get-height))

  (big-bang (void)
    [stop-when (λ (_) done?)]
    [on-tick
     (λ (_)
       (with-handlers ([exn? (thunk* (set! done? #t))])
         (define-values (board x y) (g))
         (set! last-board board)
         (set! last-x x)
         (set! last-y y)))]
    [to-draw
     (λ (_)
       (place-image
        (render last-board
                #:player-colors (const "black")
                #:highlights (hash (pt last-x last-y) "green"))
        (/ w 2)
        (/ h 2)
        (empty-scene w h)))]
    [record? #t]))
```

The {{< doc racket "with-handlers" >}} is a little ugly, but it's designed to deal with the fact that we don't return multiple values on the last call, since generators by default return the last (return) value of a function at the end. But if we wanted to make that return x and y as well, things might just get ugly, seeing as how we'd have to change all of the recursive calls. No thank you.

It's certainly pretty to watch though:

```scheme
> (queens-animate 4)
```

{{< figure src="/embeds/2014/8-queens.gif" >}}

You can see the backtracking anytime the green box jumps back and suddenly one or more of the previously place queens vanishes. It would be even neater if it could show the branching solutions, but that's a challenge for another day.

And that's it. A bit more in detail than [last time]({{< ref "2012-09-24-n-queens-in-18-lines-of-code.md" >}}), but I think it was a lot of fun. The code is available in my <a href="https://github.com/jpverkamp/chess-puzzles">chess-puzzles</a> repo on GitHub: <a href="https://github.com/jpverkamp/chess-puzzles/blob/master/puzzles/queens.rkt">queens.rkt</a>. Check it out!

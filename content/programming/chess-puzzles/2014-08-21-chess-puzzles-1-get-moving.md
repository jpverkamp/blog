---
title: 'Chess Puzzles 1: Get moving!'
date: 2014-08-21 20:00:00
programming/languages:
- Racket
- Scheme
programming/topics:
- Chess
series:
- Chess Puzzles
---
Here's something I haven't done much[^1]: chess puzzles! I'm still not sure entirely what I think about the game in general. There is certainly quite a lot of strategy, which I like, but to really get good at chess, there's also some amount of memorizing openings and closings. That's something I'm a little less thrilled with.

Still, it's the perfect sort of came to work out programming exercises with. It's a game of [[wiki:perfect information]](), so you don't have to deal with what a player knows and doesn't. The pieces have well defined, regular moves[^2] There's a fairly intense branching factor, but not insurmountable--[[wiki:Deep Blue|Deep Blue (chess computer)]]() proved that.

Anyways, enough chatter. Let's play some chess!

<!--more-->

Okay, first things first, we're going to have to lay some ground work. Despite how straight forward chess pieces are, it will still take a bit of effort to turn that into something that a computer can deal with. So first, let's work out a way of defining chess piece movement.

Here, I'm going a little ambitious. I want to be able to support arbitrary [[wiki:fairy chess pieces]](). In addition to the more standard pieces, we have  strictly more powerful pieces like the Princess (Knight + Bishop) or the Empress (Knight + Rook). Or we have alternatives, like the Camel (like the Knight, only 3:1 instead of 2:1). Or the Nightrider, which moves like the Knight, but keeps on going. I want to be able to support all of these...

Okay, first things first. A basic struct for points and another to use for a `move-sequence`:

```scheme
; Points, with associated methods; can also be used as offsets
(struct pt (x y) #:transparent)

; Move sequences for a piece; used for special flags (eg initial, capturing)
(struct move-sequence (tag moves) #:transparent)
```

The tags are mostly used for Pawns or the like, since they move one way when capturing and another when not. The rest is going to be a list of moves. So for something like the Rook, we'll have something like this:

```scheme
(list
 (move-sequence (set) (list (pt 0 1) (pt 0 2) (pt 0 3) (pt 0 4) (pt 0 5) (pt 0 6) (pt 0 7) (pt 0 8)))
 (move-sequence (set) (list (pt -1 0) (pt -2 0) (pt -3 0) (pt -4 0) (pt -5 0) (pt -6 0) (pt -7 0) (pt -8 0)))
 (move-sequence (set) (list (pt 1 0) (pt 2 0) (pt 3 0) (pt 4 0) (pt 5 0) (pt 6 0) (pt 7 0) (pt 8 0)))
 (move-sequence (set) (list (pt 0 -1) (pt 0 -2) (pt 0 -3) (pt 0 -4) (pt 0 -5) (pt 0 -6) (pt 0 -7) (pt 0 -8))))
```

When we get around to it, the idea is we can run down any of these lists until we run into something. If we run into an enemy piece, we'll allow the move; if not, we won't. Similarly, the Pawn:

```scheme
(list
 (move-sequence (set 'initial-only 'non-capture) (list (pt 0 2)))
 (move-sequence (set 'non-capture) (list (pt 0 1)))
 (move-sequence (set 'capture-only) (list (pt -1 1)))
 (move-sequence (set 'capture-only) (list (pt 1 1))))
```

On the other hand though, these are kind of a pain to type in by hand. Let's make some helper functions. First, basic movement:

```scheme
; A sequence of moves along a specific direction
; Distance is either not specified (exactly 1)
;   a number (exactly that number), n (unlimited)
;   or a range (min/max inclusive)
; Direction is either from the list '(* + > < <> = >= <= X X> X<)
;   or a list of possible single offsets
(define move
  (case-lambda
    [(direction)
     (move 1 1 direction)]
    [(distance direction)
     (if (eq? distance 'n)
         (move 1        +inf.0   direction)
         (move distance distance direction))]
    [(minimum-distance maximum-distance direction)
     (for/list ([offset (in-list (offsets-by-direction direction))])
       (move-sequence
        (set)
        (for*/list ([distance (in-range minimum-distance (+ maximum-distance 1))]
                    [p (in-value (pt* distance offset))])
                    #:break (or (> (abs (pt-x p)) (current-board-size))
                                (> (abs (pt-y p)) (current-board-size)))
          p)))]))
```

Basically, we have three different ways of specifying moves:


* `(move direction)` - moves one square in a given direction (like a pawn)
* `(move distance direction)` - moves either exactly a specific number of tiles or an unlimited number (if `distance` is `n`)
* `(move minimum-distance maximum-distance direction)` - a range of movement, so you can move between the minimum and maximum inclusive but no more or less


But what does direction mean? If it's specified as a point, that's straight forward enough, but still, we want to be able to specify these things more simply. Let's take a page out of [[wiki:Parlett's movement notation|Fairy_chess_piece#Parlett.27s_movement_notation]](). Specifically the direction specifications:


* `*` – orthogonally or diagonally (all eight possible directions)
* `+` – orthogonally (four possible directions)
* `>` – orthogonally forwards
* `<` – orthogonally backwards
* `<>` – orthogonally forwards and backwards
* `=` – orthogonally sideways (used here instead of Parlett's divide symbol.)
* `>=` – orthogonally forwards or sideways
* `<=` – orthogonally backwards or sideways
* `X` – diagonally (four possible directions)
* `X>` – diagonally forwards
* `X<` – diagonally backwards


Turn it into code:

```scheme
; Return a sequence of all possible offsets for a given direction
; Order specified front to back, left to right
(define (offsets-by-direction direction)
  `(,@(if (member direction '(*                  X X>   )) (list (pt -1  1)) '())
    ,@(if (member direction '(* + >   <>   >=           )) (list (pt  0  1)) '())
    ,@(if (member direction '(*                  X X>   )) (list (pt  1  1)) '())
    ,@(if (member direction '(* +        = >= <=        )) (list (pt -1  0)) '())
    ,@(if (member direction '(* +        = >= <=        )) (list (pt  1  0)) '())
    ,@(if (member direction '(*                  X    X<)) (list (pt -1 -1)) '())
    ,@(if (member direction '(* +   < <>      <=        )) (list (pt  0 -1)) '())
    ,@(if (member direction '(*                  X    X<)) (list (pt  1 -1)) '())
    ,@(if (pt? direction)   (list direction) '())
    ,@(if (list? direction) direction        '())))
```

We're going to set it out now: `pt` is specified as `x, y`, not `row, column`. That's something that will bite you if you don't pay attention, so make sure to be consistent.

That's enough to define most of the pieces we want.

```scheme
(define King   (move  1 '*))
(define Queen  (move 'n '*))
(define Rook   (move 'n '+))
(define Bishop (move 'n 'X))
```

Two are still left: the Knight and the Pawn. For the Knight, we need to specify something that will let us jump in arbitrary directions:

```scheme
; Make a leaper from a given offset
(define (leaper xΔ yΔ)
  (set->list
   (list->set
    `(,(pt    xΔ     yΔ )
      ,(pt (- xΔ)    yΔ )
      ,(pt    xΔ  (- yΔ))
      ,(pt (- xΔ) (- yΔ))
      ,(pt    yΔ     xΔ )
      ,(pt (- yΔ)    xΔ )
      ,(pt    yΔ  (- xΔ))
      ,(pt (- yΔ) (- xΔ))))))
```

The `list-&gt;set` and set-&gt;list` calls are to avoid duplicates. Otherwise, it's every combination of leaps in a given ratio. So if you want to define a Knight:

```scheme
(define Knight (move 1 (leaper 1 2)))
```

If you want to define the Nightrider though, it's just as simple:

```scheme
(define Nightrider (move 'n (leaper 1 2)))
```

And... that leaves us the Pawn. It's funny how perhaps the simplest of the pieces is the most complicated to define. But if you think about it, the behavior is also the longest to describe. You can move two spaces on the first move, one space any other move, but only capture diagonally. Something like this:

```scheme
(define Pawn
  (alternatives
   (on-non-capture (on-initial (move 2 '>)))
   (on-non-capture             (move 1 '>))
   (on-capture                 (move 1 'X>))))
```

What's that? We don't have `on-non-capture` / `on-capture` functions defined? Well, all we have to do is set the `tag` field we defined earlier. Something like this:

```scheme
; Set special flags for move lists
(define (set-flag flag movelist*)
  (for/list ([movelist (in-list movelist*)])
    (match-define (move-sequence flags moves) movelist)
    (move-sequence (set-add flags flag) moves)))

(define (on-initial     movelist*) (set-flag 'initial-only movelist*))
(define (on-capture     movelist*) (set-flag 'capture-only movelist*))
(define (on-non-capture movelist*) (set-flag 'non-capture  movelist*))
(define (as-locust      movelist*) (set-flag 'locust       movelist*))
```

Locusts are something we'll get to eventually. Those are pieces that move like checkers: they capture by jumping. Other than that, we just need the `alternatives`:

```scheme
; Merge multiple move lists by allowing any of them
(define (alternatives . list*)
  (apply append list*))
```

Feels like cheating. And there we have the pawn:

```scheme
> Pawn
(list
 (move-sequence (set 'initial-only 'non-capture) (list (pt 0 2)))
 (move-sequence (set 'non-capture) (list (pt 0 1)))
 (move-sequence (set 'capture-only) (list (pt -1 1)))
 (move-sequence (set 'capture-only) (list (pt 1 1))))
```

Sweet.

Okay, what about other kinds of pieces. Say... the Aanca. That's a piece that moves one square orthogonally than diagonally outwards. It's a bit complicated by the fact that we don't want to double back with the diagonals and we need one more function. A sequencer:

```scheme
; Merge multiple move lists by doing one and then the next, each relative to the previous endpoint
(define (and-then first* rest*)
  (for*/list ([first (in-list first*)]
              [rest  (in-list rest*)])
    (match-define (move-sequence first-flags first-moves) first)
    (match-define (move-sequence rest-flags  rest-moves)  rest)
    (define offset (last first-moves))
    (move-sequence
     (set-union first-flags rest-flags)
     (append first-moves (map (λ (each) (pt+ offset each)) rest-moves)))))
```

Now we can have the Aanca:

```scheme
; Move one square like a rook, followed by any number of spaces diagonally outwards
(define Aanca
  (alternatives
   (and-then (move 1 '>) (move 'n 'X>))
   (and-then (move 1 (pt 1 0))  (alternatives (move 'n (pt  1 -1))
                                              (move 'n (pt  1  1))))
   (and-then (move 1 '<) (move 'n 'X<))
   (and-then (move 1 (pt -1 0)) (alternatives (move 'n (pt -1 -1))
                                              (move 'n (pt -1  1))))))
```

And that's it. We can define a whole pile of the other [[wiki:Fairy chess pieces]]():

```scheme
(define Adjutant     (move  1 '<>))
(define Advisor      (move  1 'X))
(define Alfil        (move  1 (leaper 2 2)))
(define Afilrider    (move 'n (leaper 2 2)))
(define Alibaba      (alternatives (move 'n (leaper 2 2)) (move 'n (leaper 0 2))))
(define Amazon       (alternatives (move 1 (leaper 1 2)) (move 'n '*)))
(define Antelope     (move  1 (leaper 3 4)))
(define Archbishop   (alternatives (move 'n 'X) (move 1 (leaper 1 2))))
(define ArrowPawn    (alternatives (on-non-capture (move 1 '+))
                                   (on-capture (move 1 'X))))
(define Backslider   (move  1 '<))
(define Banshee      (alternatives (move 'n 'X) (move 'n (leaper 1 2))))
(define Bede         (alternatives (move 'n 'X) (move 'n (leaper 0 2))))
(define BerolinaPawn (alternatives (on-non-capture (on-initial (move 2 'X>)))
                                   (on-non-capture (move 1 'X>))
                                   (on-capture (move 1 '>))))
...
```

(Feel free to submit a <a href="https://github.com/jpverkamp/chess-puzzles/pulls">pull request</a> if you want to add more. :smile:)

Oof. That's a lot of code. I think that's about enough for today.

You can see the full code on GitHub: <a href="https://github.com/jpverkamp/chess-puzzles">jpverkamp/chess-puzzles</a>. Warning though: I'm a bit further ahead code-wise than blog-wise. That way lies spoilers...

Speaking of which:

{{< figure src="/embeds/2014/chessboard.png" >}}

:smile:

[^1]: Okay, [a little]({{< ref "2013-02-01-1gam-chesslike-1-0-did-it.md" >}}).
[^2]: For the moment, we'll ignore castling and [[wiki:en passant]]().
---
title: 'Chess Puzzles 2: Board?'
date: 2014-08-28 20:00:00
programming/languages:
- Racket
- Scheme
programming/topics:
- Chess
series:
- Chess Puzzles
---
Now that we've got [Ludum Dare]({{< ref "2013-05-21-ludum-dare-26-vtanks-results.md" >}}) out of the way, back to chess! [Last time]({{< ref "2014-08-21-chess-puzzles-1-get-moving.md" >}}), we defined all of the pieces, which is all well and good, but what we really need is a board. More specifically, we want something that can:


* Represent an 8x8 chess board, storing the location of pieces (including the owner of each)
* Add logic for collisions, so that when moving a piece, you cannot move through others or capture allies[^1]
* Add rendering code to display the current chess board (must be flexible enough to handle arbitrary glyphs for [[wiki:fairy chess]]() pieces)


I think that's about enough for the moment. Let's do it!

<!--more-->

First things first, let's create a representation of the board. We'll start with only regular grids, although theoretically it should be possible to define arbitrary connections. That would mess somewhat with the move definitions we have, so let's not.

First, the board:

```scheme
; Stored as a vector of vectors where every element is either:
; (player, piece) if there is a piece there
; #f if empty
(struct board (pieces data) #:transparent)
```

So what we should have is something like this:

```scheme
(define (make-standard-board)
  (board (hash 'Rook   Rook
               'Knight Knight
               'Bishop Bishop
               'Queen  Queen
               'King   King
               'Pawn   Pawn)
         '#(#((Black Rook) (Black Knight) (Black Bishop) (Black Queen)
              (Black King) (Black Bishop) (Black Knight) (Black Rook))
            #((Black Pawn) (Black Pawn) (Black Pawn) (Black Pawn)
              (Black Pawn) (Black Pawn) (Black Pawn) (Black Pawn))
            #(#f #f #f #f #f #f #f #f)
            #(#f #f #f #f #f #f #f #f)
            #(#f #f #f #f #f #f #f #f)
            #(#f #f #f #f #f #f #f #f)
            #((White Pawn) (White Pawn) (White Pawn) (White Pawn)
              (White Pawn) (White Pawn) (White Pawn) (White Pawn))
            #((White Rook) (White Knight) (White Bishop) (White Queen)
              (White King) (White Bishop) (White Knight) (White Rook)))))
```

Vectors will allow both `O(1)` reading of elements, but also a nice way of doing mutation. I'm just going to go right out now and say that I'll allow mutating the board, although I might make a non-mutable version that copies if I have a chance[^2].

Next, a getter and a sanity check (which should make it cleaner to generate moves):

```scheme
; Test if a point is on the given board
(define (on-board? b p)
  (match-define (board pieces data) b)
  (match-define (pt x y) p)
  (and (<= 0 x (- (vector-length (vector-ref data 0)) 1))
       (<= 0 y (- (vector-length data) 1))))

; Get the current player/piece at a square
(define (board-ref b p)
  (match-define (board pieces data) b)
  (match-define (pt x y) p)
  (cond
    [(on-board? b p)
     (vector-ref (vector-ref data y) x)]
    [else
     #f]))
```

And finally, a setter. In this case, it doesn't make sense to just set a single piece (except in set up I guess?)[^3]. So instead, we will allow movement, overwriting whatever is at the target square:

```scheme
; Move a piece from one square to another, overwriting whatever is in the destination square
(define (board-move! b src dst)
  (match-define (board pieces data) b)
  (match-define (pt src-x src-y) src)
  (match-define (pt dst-x dst-y) dst)
  (define piece (board-ref data src))
  (vector-set! (vector-ref data dst-y) dst-x piece)
  (vector-set! (vector-ref data src-y) src-x #f))
```

And that's about all we need for the board representation. Let's check out rendering next, since it should (theoretically) make debugging the move list generation much better.

First, let's generalize the tile for a piece to a `glyph`:

```scheme
; The hash associating piece names with glyphs
(define current-glyphs (make-parameter #f))

; A single glyph containing a string and the rotation (default to upright)
(struct glyph (character rotation) #:transparent)
(define (make-glyph character [rotation 0])
  (glyph (~a character) rotation))

; Render a single character with some sanity checking for different types
(define (render-glyph/pict g tile-size)
  (cond
    [(glyph? g)
     (match-define (glyph character rotation) g)
     (rotate (text character 'default (* 3/4 tile-size)) rotation)]
    [else
     (render-glyph/pict (make-glyph g) tile-size)]))
```

This way, we can specify characters in several different ways. We can pass just about anything directly and use the {{< doc racket "~a" >}} function to 'string' it. Or we can pass both the former and a rotation. That will let us do things like an inverted knight being the representation for the nightrider, etc.

One thing that amuses me entirely too much about this?

```scheme
(define (set-standard-glyphs)
  (current-glyphs (hash 'Rook   "♜"
                        'Knight "♞"
                        'Bishop "♝"
                        'Queen  "♛"
                        'King   "♚"
                        'Pawn   "♟")))
```

Those are unicode characters for the chess symbols. Nice. :smile:

Okay, so we have a way to represent a single tile, what do we have to do to render all of them? Well, as often before, we can use the {{< doc racket "pict" >}} library:

```scheme
; Render a board to a pict with the given tile size
(define (render/pict b #:tile-size [tile-size 20])
  ; Sanity check and unpack, we don't care about the actual pieces at this point
  (when (not (current-glyphs))
    (error 'render/pict "must specify (current-glyphs) as a hash of name -> glyph"))
  (match-define (board _ board-data) b)

  ; Render each tile into a list of lists
  (define tiles
    (for/list ([row-index (in-naturals)]
               [row       (in-vector board-data)])
      (for/list ([col-index (in-naturals)]
                 [col       (in-vector row)])
        ; Get the background tile
        ; TODO: Parameterize the tile colors
        ; TODO: Figure out how to do borders
        (define tile-color
          (cond
            [(even? (+ row-index col-index))
             "LightGray"]
            [else
             "DarkGray"]))
        (define tile (colorize (filled-rectangle 20 20) tile-color))

        (cond
          ; If there is a piece here, render the piece, colorize based on the player,
          ; and overlay on the tile
          [col
           (match-define (list player piece) col)
           (define glyph
             (render-glyph/pict (hash-ref (current-glyphs) piece) tile-size))
           (cc-superimpose tile (colorize glyph (~a player)))]
          ; If not, just return the empty tile
          [else
           tile]))))

  ; Smash together all the lists of lists
  (apply vc-append
         (for/list ([row (in-list tiles)])
           (apply hc-append row))))
```

Okay, that looks like a lot, but most of it is comments. Basically, we loop over the board (the pair of {{< doc racket "for/list" >}}), building nested lists. Then, for each tile, we determine if we're on a white or black square (light and dark gray so that the white and black actually stand out). After that, we get the string from the `glyph` and render it as {{< doc racket "text" >}}. There's one thing I haven't done yet: support strings of multiple characters. Essentially, I would scale horizontally to make it be the correct width. Good enough for now though.

So how does it work? Well combine `make-standard-board` and `render/pict`:

```scheme
> (render/pict (make-standard-board))
```

{{< figure src="/embeds/2014/initial-board.png" >}}

Fair enough. But to visualize, what we really want is an ability to show off certain squares. So let's add a `#:highlight` keyword parameter of a hash of points to colors to color them specially. Something like this:

```scheme
; Render a board to a pict with the given tile size
(define (render/pict b #:tile-size [tile-size 20] #:highlights [special-tiles (hash)])
  ...

  ; Get the background tile
  ; TODO: Parameterize the tile colors
  ; TODO: Figure out how to do borders
  (define tile-color
    (cond
      [(hash-ref special-tiles (pt col-index row-index) #f)
       => identity]
      [(even? (+ row-index col-index))
       "LightGray"]
      [else
       "DarkGray"]))

  ...)
```

This way, we can highlight any square we want:

```scheme
> (render/pict (make-standard-board)
               #:highlights (hash (pt 2 2) "green"
                                  (pt 5 2) "green"
                                  (pt 2 4) "red"
                                  (pt 3 5) "red"
                                  (pt 4 5) "red"
                                  (pt 5 4) "red"))
```

{{< figure src="/embeds/2014/highlights.png" >}}

(Remember that indices are 0-based)

Shiny!

Okay, that's enough to test. Let's work on a function to determine moves. We want something like this:

```scheme
; Return a list of moves that a piece can make on the given board given it's origin point
(define (moves-from b origin #:initial [initial #f])
  ...)
```


We'll have a flag if the piece is on the initial turn, otherwise we pull everything out (like which player we're dealing with) from the piece on the board:

```scheme
...
  (cond
    [(board-ref b origin)
     => (λ (ls)
          (match-define (list player name) ls)
          (match-define (piece _ moves) (hash-ref pieces name))

          ; White has inverse moves since they're moving 'up'
          ; TODO: Generalize to more players
          ; TODO: This moves the wrong way if you have 'left only' pieces
          (define player-multiplier
            (case player
              [(BLACK Black black)  1]
              [(WHITE White white) -1]
              [else     1]))

  ...
```

This is the case when we have a piece (if not, the location is `#f`). If we have that, we unpack the piece and then determine which player we have. For the black player, we're moving down on the board / up in the y-coordinate, so the numbers are correct. Otherwise, we'll multiply moves my negative one. This has the effect of reflecting the moves. Unfortunately, it's on both axes, but at least with any piece I've seen, that doesn't actually matter.

Next, we're going to take the move sequences we generated last time and filter each one so that we only include the moves from that sequence that are viable. For that, we first need to find the `first-target`--the first piece that we would hit if moving along this path.

```scheme
...
          (define move-sublists
           (for*/list ([move-seq (in-list moves)])
             (match-define (move-sequence tags original-offset*) move-seq)
             (define offset* (map (λ (offset) (pt* player-multiplier offset)) original-offset*))

             ; Find the first target
             (define first-target
               (for/first ([i (in-naturals)]
                           [offset (in-list offset*)]
                           #:when (board-ref b (pt+ origin offset)))
                 (list i (board-ref b (pt+ origin offset)))))

             ; If the first target belongs to the owner, remove it (no self captures)
             ; TODO: Add an option for self-captures
             (define self-capture
               (and first-target
                    (eq? (first (second first-target)) player)))
             ...
```

Another amusing option that I'm sure there are fairy chess pieces that use: self-captures.

Next, we want to unfold those lists based on how we found the `first-target`:

```scheme
...
             (map (λ (offset) (pt+ origin offset))
                  (cond
                    ; Bail out if we're initial only but not on the initial move
                    [(and (set-member? tags 'initial-only) (not initial))
                     (list)]
                    ; If we're capturing only, can only move if we have a target
                    ; and to that square
                    [(set-member? tags 'capture-only)
                     (if (and first-target (not self-capture))
                         (list (list-ref offset* (first first-target)))
                         (list))]
                    ; If we're not capturing, get everything up until the target
                    ; (or everything if no target)
                    [(set-member? tags 'non-capture)
                     (if (and first-target (> (first first-target) 0))
                         (take offset* (- (first first-target) 1))
                         offset*)]
                    ; If we're a locust, we have to check the space after the self
                    ; target is empty
                    [(set-member? tags 'as-locust)
                     (cond
                       [(and first-target
                             (not self-capture)
                             (> (length offset*) (+ (first first-target) 1)))
                        (define next-target
                          (board-ref b (list-ref offset* (+ (first first-target) 1))))
                        (if (not next-target)
                            (list (list-ref offset* (+ 1 (first first-target))))
                            (list))]
                       [else
                        (list)])]
                    ; If the target is an enemy, capture it and stop
                    ; Otherwise, if the target is a piece but we own, don't land there
                    [first-target
                     (if self-capture
                         (if (> (first first-target) 0)
                             (take offset* (first first-target))
                             (list))
                         (take offset* (+ (first first-target) 1)))]
                    ; Otherwise, include the entire range
                    [else
                     offset*]))))

          ...
```

Oof. That's a lot of code. But luckily, each case is fairly straight forward. We remove non-initial moves (like for pawns), set the capturing / non-capturing conditions, or move like a locust (that have to jump to capture). And then finally, if the first thing is our own, just cut that off (this is where a self-capture tag would come in).

And then to finish it off:

```scheme
...
          ; Stick all the lists together since we no longer care how they got there
          ; And remove all moves that jump off of the board somehow
          (filter (λ (p) (on-board? b p)) (apply append move-sublists)))]
    [else
     '()]))
```

Bam. We have moves. Let's try it out:

```scheme
; Black pawn
> (moves-from (make-standard-board) (pt 3 1) #:initial #t)
(list (pt 3 3) (pt 3 2))

; White knight
> (moves-from (make-standard-board) (pt 6 7))
(list (pt 7 5) (pt 5 5))
```

And using our highlighting code:

```scheme
> (let* ([board (make-standard-board)]
         [highlights (for/hash ([pt (moves-from board (pt 3 1) #:initial #t)])
                        (values pt "green"))])
    (render/pict board #:highlights highlight))
```

{{< figure src="/embeds/2014/moves-pawn.png" >}}

```scheme
> (let* ([board (make-standard-board)]
         [highlights (for/hash ([pt (moves-from board (pt 6 7))])
                        (values pt "green"))])
    (render/pict board #:highlights highlight))
```

{{< figure src="/embeds/2014/moves-knight.png" >}}

Shiny!

Looks like it's working great. Let's generate images for all of the pieces:

```scheme
> (for/list ([piece (in-list '(Pawn Rook Knight Bishop Queen King))])
    (define test-board
      (board (hash 'Rook   Rook
                   'Knight Knight
                   'Bishop Bishop
                   'Queen  Queen
                   'King   King
                   'Pawn   Pawn)
             `#(#(#f #f #f #f #f #f #f #f)
                #(#f #f #f #f #f #f (White Pawn) #f)
                #(#f #f #f #f (White Pawn) #f #f #f)
                #(#f #f #f (White Pawn) #f (Black Pawn) #f #f)
                #(#f #f #f #f (White ,piece) #f #f (Black Pawn))
                #(#f #f #f #f (Black Pawn) #f #f #f)
                #(#f #f #f #f #f #f (Black Pawn) #f)
                #(#f #f #f #f #f #f #f #f))))

    (define highlights
      (for/hash ([pt (in-list (moves-from test-board (pt 4 4)))])
        (values pt "green")))

    (render/pict test-board #:highlights highlights))
```

{{< figure src="/embeds/2014/demo-pawn.png" >}}
{{< figure src="/embeds/2014/demo-rook.png" >}}
{{< figure src="/embeds/2014/demo-knight.png" >}}
{{< figure src="/embeds/2014/demo-bishop.png" >}}
{{< figure src="/embeds/2014/demo-queen.png" >}}
{{< figure src="/embeds/2014/demo-king.png" >}}

That is cool. I love it when something works like that!

(Note: Yes, the king can currently move into check. That's on the list of things to fix yet, along with castling and en passant.)

Here's actually a lesson too, until I generated those images for this post, I actually had a bug where I wasn't stopping after hitting an enemy piece. Good thing I checked otherwise who knows what would have happened?

And that's about it for today. We now have move lists, a board, and some rendering. Should be enough so that next time we can *actually* write up a chess puzzle. Third time's a charm, eh?

If you'd like to see the entire code, it's on GitHub: <a href="https://github.com/jpverkamp/chess-puzzles">jpverkamp/chess-puzzles</a>

[^1]: I need to add an option for that :smile:
[^2]: Hey, it's the schemey thing to do
[^3]: And I bet there are fairy chess variations with 'spawners' or the like...
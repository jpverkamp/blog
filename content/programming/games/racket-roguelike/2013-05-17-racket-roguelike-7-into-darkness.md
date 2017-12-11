---
title: 'Racket Roguelike 7: Into darkness!'
date: 2013-05-17 14:00:45
programming/languages:
- Racket
programming/sources:
- 7DRL
programming/topics:
- Games
- Roguelikes
series:
- Racket Roguelike
---
When I was playing Racket Roguelike earlier this week[^1], I realized something: I can see everything. There are no surprises, no mystery, no *darkness*

Let's fix that.

<!--more-->

(If you'd like to start at the beginning, click here: [Racket Roguelike 1: A GUI, screens, I/O, and you!]({{< ref "2013-04-04-racket-roguelike-1-a-gui-screens-i-o-and-you.md" >}}))

This week, we want to add a dynamic lighting system to the game. If we were using a pre-built framework (like Doryen's excellent [AsciiPanel]({{< ref "2013-03-28-writing-a-roguelike-in-racket-day-0.md" >}}) some day}. But that's not the case. Luckily, the framework we've built already makes lighting relatively easy.

First, we need some way of representing which tiles should be lit. Technically, we could calculate this on the fly every frame. This isn't actually a terrible way of doing things and might just be more efficient than what we're doing (don't even bother rendering tiles you can't see), but since we want to have a 'fog of war' type system--where you can see the terrain you've passed, just not what's there--that won't quite work.

Instead, let's add it to the `tile` definitions:

```scheme
; levels.rkt

(define-thing tile
  [character #\space]
  [color "black"]
  [items '()]
  [lighting 'dark]    ; Dark: Invisible; Fog: Only show tile, not NPC or item; Lit: Everything
  [walkable #f]       ; Can the player walk on this tile?
  )
```

As it says in the comment, we have a `lighting` parameter with three possible states:


* `dark` - don't draw the tile
* `fog` - draw the tile, but no items or NPCs in it (used once we see a tile then leave)
* `lit` - draw the tile, items, and NPCs (used when the player is nearby)


Easy enough. But how do we actually add that to our drawing function? Head over to *game-screen.rkt*:

```scheme
; game-screen.rkt

(define gray-background (make-object color% 32 32 32))

...

; Draw the tiles around the player
(for* ([xi (in-range (send canvas get-width-in-characters))]
       [yi (in-range (send canvas get-height-in-characters))])
  (define x/y (recenter canvas (- (thing-get player 'location) (pt xi yi))))
  (define tile (send world tile-at (pt-x x/y) (pt-y x/y)))
  (define lighting (thing-get tile 'lighting 'lit))
  (cond
    ; Draw nothing on dark tiles
    [(eq? lighting 'dark)
     (void)]
    ; If it's in fog, draw with a gray background
    [(eq? lighting 'fog)
     (send canvas write
           (thing-get tile 'character)
           xi yi
           (thing-get tile 'color) gray-background)]
    ; If it's lit but there are no items, draw the tile
    [(null? (thing-get tile 'items '()))
     (send canvas write
           (thing-get tile 'character)
           xi yi
           (thing-get tile 'color))]
    ; If it's lit and there are items, draw the item
    [else
     (send canvas write
           (thing-get (car (thing-get tile 'items)) 'character)
           xi yi
           (thing-get (car (thing-get tile 'items)) 'color))]))
```

Basically, we draw nothing on dark tiles. This relies on the `clear` just above this code. If it's foggy, we have a background, defined at the top of the file[^2]. Otherwise, we fall back on the methods that we already had.

Next, we need to actually calculate this lighting. Essentially, every tile starts dark. Then, if a tile is near to the player, light it up. If it's already lit but no longer near the tile, fade to fog. For now, we're just going to use a simple radius around the player (parameterized below). Here's the new `update-lighting` function and friends:

```scheme
; entities.rkt

; game-screen.rkt
(define-thing entity
  ...
  [view-range 5])

; Draw the game itself.
(define/override (draw canvas)
  (define player (send world get-player))
  (send canvas clear)

  ; Update lighting
  (send world update-lighting)

  ...)

; world.rkt

; Update lighting
(define/public (update-lighting)
  ; Turn any lit tiles to fog
  ; Turn any tiles within the player's view limit to lit
  (define player-location (thing-get player 'location))
  (define player-view (thing-get player 'view-range 5))
  (for-tile
   (lambda (x y tile)
     (cond
       ; Light tiles near the player
       [(<= (distance player-location (pt x y)) player-view)
        (thing-set! tile 'lighting 'lit)]
       ; Fog previously lit tiles
       [(eq? 'lit (thing-get tile 'lighting))
        (thing-set! tile 'lighting 'fog)]
       ; Otherwise do nothing
       ))))
```

For that, we need the `for-tile` function. You can check it out <a href="https://github.com/jpverkamp/racket-roguelike/blob/master/src/levels.rkt">on GitHub</a>, but essentially it takes a function of the form `(lambda (x y tile) ...)` and applies it to each tile on the current level. It might[^3] get inefficient on more explored levels, but if people keep heading down, we should be good. So in this case, we'll just light the area around the player. How does that look?

{{< figure src="/embeds/2013/simple-lighting.png" >}}

Starting out, not too bad. We're out in the middle of a nice grass field like always. Just this time, we can't see much of it. Perhaps it's night time?

{{< figure src="/embeds/2013/simple-fog.png" >}}

Wander around a bit until we find a way down. You can see the gray background of the fog. That actually looks pretty nice, particularly as you're moving around.

{{< figure src="/embeds/2013/into-the-caves.png" >}}

Okay, now we're into the caves. Let's explore for a bit.

{{< figure src="/embeds/2013/this-is-a-problem.png" >}}



Hmm. Well, this is a problem. It turns out... we can see right through walls. Perhaps we should work on that a bit.

This is when a pre-built framework would *really* come in handy. But the algorithm isn't too bad. Essentially, we want {{< wikipedia "raycasting" >}}. We'll start with a series of lines out from the player and light tiles as we go. If we hit something that can't be lit up, stop. Sounds like a nicely recursive function to me!

Before that, let's modify the tile definitions again. We'll add the `solid` property. If a tile is `solid` (like a wall or a tree), you can't see through it. Otherwise (like empty space or over water), you can.

```scheme
; levels.rkt

(define-thing tile
  [character #\space]
  [color "black"]
  [items '()]
  [lighting 'dark]    ; Dark: Invisible; Fog: Only show tile, not NPC or item; Lit: Everything
  [walkable #f]       ; Can the player walk on this tile?
  [solid #f]          ; Does this tile block light?
  )
```

So how do we write a raycasting function?

The basic idea[^4] is to start with four rays, one in each of the cardinal directions. Give each ray its own direction. Then as we pass each tile, branch out in each direction for a total of three branches per iteration. It's certainly not optimal (we'll light some tiles more than once), but it does look nice.

```scheme
; world.rkt

; Update lighting
(define/public (update-lighting)
  ; Turn any lit tiles to fog
  (for-tile
   (lambda (x y tile)
     (cond
       [(eq? 'lit (thing-get tile 'lighting 'dark))
        (thing-set! tile 'lighting 'fog)])))

  ; Spread lighting from the player
  ; x/y current tile to light
  ; xd/yd direction to spread light:
  ;  if xd != 0, spread to (x+xd y-1) (x+xd y) (x+xd y+1)
  ;  if yd != 0, spread to (x-1 y+yd) (x y+yd) (x-1 y+yd)
  ; spread is initially set to player's light radius
  (define (spread-light x y xd yd spread)
    ; Light the current tile
    (define tile (get-tile x y))
    (thing-set! tile 'lighting 'lit)

    ; Recur
    (cond
      ; Don't spread pass solid tiles (spread to them though)
      ; Don't recur past the spread (vision range) value
      [(or (<= spread 0) (thing-get tile 'solid #f))
       (void)]
      ; Spread in the x direction
      [(not (= xd 0))
       (spread-light (+ x xd) (- y 1) xd yd (- spread 1.41))
       (spread-light (+ x xd) y       xd yd (- spread 1.00))
       (spread-light (+ x xd) (+ y 1) xd yd (- spread 1.41))]
      ; Spread in the y direction
      [else
       (spread-light (- x 1) (+ y yd) xd yd (- spread 1.41))
       (spread-light x       (+ y yd) xd yd (- spread 1.00))
       (spread-light (+ x 1) (+ y yd) xd yd (- spread 1.41))]))

  ; Spread in the four directions
  (let ([player-x (pt-x (thing-get player 'location))]
        [player-y (pt-y (thing-get player 'location))]
        [player-v (thing-get player 'view-range 5)])
    (spread-light player-x player-y -1  0 player-v)
    (spread-light player-x player-y  1  0 player-v)
    (spread-light player-x player-y  0 -1 player-v)
    (spread-light player-x player-y  0  1 player-v)))
```

Hopefully that all makes sense. One sneaky trick is reducing the `spread` by 1 on the orthogonal moves and 1.41 (roughly {{< inline-latex "sqrt(2)" >}}) on the diagonals. This will give us a nice circle.

Let's see what an effect that has on the game:

{{< figure src="/embeds/2013/nice-circle.png" >}}

Starting out, we have a nice circle. So far, it looks pretty much the same as it did last time.

{{< figure src="/embeds/2013/trees-cast-shadows.png" >}}

Shadows! I can't tell you how excited this makes me. :smile:

{{< figure src="/embeds/2013/over-troubled-waters.png" >}}

And it works perfectly with water as well. We can see over the water, but we can't walk through it.

{{< figure src="/embeds/2013/missing-something.png" >}}

Unfortunately though, I haven't had any luck yet finding a staircase...

{{< figure src="/embeds/2013/no-more-xray-vision.png" >}}

Finally, we're down a level. It's nice to see[^5]: no more x-ray vision! It does look a bit weird to have all the nice thin walls around, but it looks a lot better once you get used to it.

{{< figure src="/embeds/2013/there-are-rats.png" >}}

Theoretically, the player shouldn't be able to hear updates from entities that aren't visible. That would actually be pretty easy to implement (just check for the lighting in the logging function), but for the moment, I like the atmosphere it gives.

{{< figure src="/embeds/2013/still-no-rats.png" >}}

All that time wandering about and I still haven't actually found any of those rats to fight. I wanted to show that it won't draw them unless they're in a lit area. Sigh. So it goes.

Well, that's all we have for today. It's kind of amazing how much difference so few lines can make[^6].

As always, if you'd like to see all of the code for this project, you can do so on GitHub:
- <a title="Racket Roguelike on GitHub" href="https://github.com/jpverkamp/racket-roguelike/tree/day-7">Racket Roguelike - Day 7</a>
- <a title="Racket Roguelike on GitHub" href="https://github.com/jpverkamp/racket-roguelike">Racket Roguelike - Up to date</a>

If you'd like to try it yourself, you'll need to have both <a href="http://git-scm.com/">Git</a> and <a href="http://racket-lang.org/">Racket</a> and run the following series of commands:

```bash
git clone git://github.com/jpverkamp/racket-roguelike.git
cd racket-roguelike
git checkout day-7
git submodule init
git submodule update
racket main.rkt
```

**Edit:**

It seems that the submodules wondered off at some point. Instead, you can install the three libraries this uses directly using {{< doc racket "pkg" >}}, and then run the code:

```bash
raco pkg install github://github.com:jpverkamp/ascii-canvas/master
raco pkg install github://github.com:jpverkamp/noise/master
raco pkg install github://github.com:jpverkamp/thing/master
git clone git://github.com/jpverkamp/racket-roguelike.git
cd racket-roguelike
git checkout day-7
racket main.rkt
```

For part 8, click here: [Racket Roguelike 8: A million words!]({{< ref "2013-06-21-racket-roguelike-8-a-million-words.md" >}})



[^1]: Always a good sign when you find yourself actually playing your own game...
[^2]: And defined only once to save just a bit on performance; we're going to have to look at that soon...
[^3]: Read: will
[^4]: Which may or may not be the standard way of doing it
[^5]: Believe it or not, pun not intended
[^6]: According to the git diff, 26 lines removed and 111 added
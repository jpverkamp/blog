---
title: 'Racket Roguelike 10: Levels via automata!'
date: 2013-07-05 14:00:29
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
[Last week]({{< ref "2013-06-28-racket-roguelike-9-daedalus-wrath.md" >}}) we made mazes on a regular grid using the [noise generators]({{< ref "2013-04-11-perlin-and-simplex-noise-in-racket.md" >}}). That was pretty neat, but it got me thinking. What other ways do we have to procedurally generate interesting level patterns?

<!--more-->

Well, one option would be to use [[wiki:cellular automaton]](). I've written about them [before]({{< ref "2012-10-03-elementary-cellular-automaton.md" >}}), but in summary, they're basically applying a set of rules to a regular grid resulting in emergent features. In this case, our rule will be simple. Start with an empty grid seeded with a random central tile. From there, randomly generate new tiles, making them walkable if and only if there is 1-3 walkable tiles around them. This means that they have to be connected and they can't be too connected (allowing for branches but nothing more).

The first problem we have with that is that our current setup doesn't really allow for taking a tile's neighbors into account when generating content. So we'll have to directly access the level's tile hash. It's suboptimal (since we're breaking the abstraction), but it will work.

The second problem is that we can't rely on the normal terrain generation to work since it's too regular. Since we build the terrain when it's seen and always from top left to bottom right, we'll always get the same (poor) levels. We can get around this though. Any time the level generation function is called that means we're generating a new region. So clear the current region around that tile and then repeatedly randomly fill it back in.

So how does the code for this look?

```scheme
; Use a cellular automaton to generate levels
(define (cellular seed x y)
  ; Get the current level
  (define current-level (get-level (current-depth)))

  ; Helper to count neighboring grass tiles
  (define (grass? at)
    (eq? #\. (thing-get (hash-ref current-level at empty) 'character #\space)))
  (define (count at)
    (for*/sum ([xi (in-range -1 2)]
               [yi (in-range -1 2)]
               #:unless (= 0 xi yi))
      (if (grass? (+ at (pt xi yi))) 1 0)))

  ; Now randomly set some percentage of the surrounding tiles
  (define region-size 10)

  ; Clear the area first
  (for* ([xi (in-range (- x region-size) (+ x region-size 1))]
         [yi (in-range (- y region-size) (+ y region-size 1))])
    (hash-set! current-level (pt xi yi) (make-thing wall)))

  ; Set the center tile
  (hash-set! current-level (pt x y) (make-thing grass))

  ; Random grow
  (for ([i (in-range (* region-size region-size region-size))])
    ; Choose a random point from the nearby area
    (define new-pt (+ (pt x y)
                      (pt (- (random (* region-size 2)) region-size)
                          (- (random (* region-size 2)) region-size))))

    ; Set the new tile if we have 3 or less neighbors
    ; And this tile hasn't already been set
    ; Some become stairs instead
    (when (<= 1 (count new-pt) 2)
      (hash-set! current-level new-pt
                 (if (zero? (random 100))
                     (make-thing stairs-up)
                     (make-thing grass)))))

  ; Return our tile
  (hash-ref current-level (pt x y)))
```

Theoretically, the comments should be all you need to understand what's going on.

So how does it look?

{{< figure src="/embeds/2013/Cellular-growth-1.png" >}}

Basically, we have a nice warren of tightly curving caves. It really reminds me a fair bit of Sandbox. Some day I want to go back to that...

So that's one non-noise based level generation script. What else can we do?

This time I'm going back way to the dawn of my computing experience. Something nearing two decades ago, I started programming in [[wiki:Qbasic]]() (yup). One of my favorite programs from that time? Bugs. Basically, I started a bunch of random points on the screen, each of which would [[wiki:random walk]]() for a while, drawing a line. In the end, you'd get something like this:

<a href="https://upload.wikimedia.org/wikipedia/commons/thumb/3/39/Random_walk_in2D_closeup.png/510px-Random_walk_in2D_closeup.png"><img alt="" src="https://upload.wikimedia.org/wikipedia/commons/thumb/3/39/Random_walk_in2D_closeup.png/510px-Random_walk_in2D_closeup.png" class="alignnone" width="255" height="300" /></a>

That looks a lot like the sorts of caves we might want to generate. So let's do it!

```scheme
; Generate levels using skittering bugs
(define (bugs seed x y)
  (define current-level (get-level (current-depth)))

  ; When a tile is requested, spread out from it for a while
  (let loop ([i 0] [x x] [y y])
    (define at (pt x y))

    ; Clear unset neighbors
    (for* ([xi (in-range -1 2)] [yi (in-range -1 2)])
      (define ati (+ at (pt xi yi)))
      (when (not (hash-has-key? current-level ati))
        (hash-set! current-level ati (make-thing wall))))

    ; Set the current tile
    (hash-set! current-level at
               (if (zero? (random 100))
                   (make-thing stairs-up)
                   (make-thing grass)))

    ; Wonder around
    (when (< i 10)
      (loop (+ i 1) (+ x (random 3) -1) (+ y (random 3) -1))))

  ; Return the tile
  (hash-ref current-level (pt x y)))
```

Basically, we use the same idea as before. When the function is called, spread out from there. That stops the nearby area from having to generate. So we get nice regions centered on each non-generated text.

And how does this one look?

{{< figure src="/embeds/2013/Bug-growth.png" >}}

It looks a lot like the cellular growth, but this time we have a lot more open caverns (as expected, each generating block will tend to form a room). What's nice is that there are all sorts of parameters to tweak. So we could make all sorts of rooms.

In any case, it's entirely too late now, so I really should be getting to sleep. One of these days I'll work ahead on these. :smile:

As always, if you'd like to see all of the code for this project, you can do so on GitHub:
- <a title="Racket Roguelike on GitHub" href="https://github.com/jpverkamp/racket-roguelike/tree/day-10">Racket Roguelike - Day 10</a>
- <a title="Racket Roguelike on GitHub" href="https://github.com/jpverkamp/racket-roguelike">Racket Roguelike - Up to date</a>

If you'd like to try it yourself, you'll need to have both <a href="http://git-scm.com/">Git</a> and <a href="http://racket-lang.org/">Racket</a> and run the following series of commands:

```bash
git clone git://github.com/jpverkamp/racket-roguelike.git
cd racket-roguelike
git checkout day-10
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
git checkout day-10
racket main.rkt
```



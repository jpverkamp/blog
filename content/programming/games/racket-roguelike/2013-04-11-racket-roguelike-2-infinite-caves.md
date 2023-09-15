---
title: 'Racket Roguelike 2: Infinite caves!'
date: 2013-04-11 14:05:25
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
When [last we met]({{< ref "2013-04-04-racket-roguelike-1-a-gui-screens-i-o-and-you.md" >}}), we had a working GUI with the player's `@` walking about. Today, we're going to add somewhere for the player to wander about[^1].

<!--more-->

If you'd like to start at the beginning, click here: [Racket Roguelike 1: A GUI, screens, I/O, and you!]({{< ref "2013-04-04-racket-roguelike-1-a-gui-screens-i-o-and-you.md" >}})

The bulk of today's post relies on having noise generating functions (nope, not [[wiki:Noise|that noise]]()). That was actually enough for a <a title="Perlin and simplex noise in Racket" href="http://blog.jverkamp.com/2013/04/11/perlin-and-simplex-noise-in-racket/?preview=true">post all its own</a>, so if making some noise sounds at all interesting, check it out. Otherwise, we're just going to add my new <a title="noise on GitHub" href="https://github.com/jpverkamp/noise">noise library</a> as a Git submodule to the project (so you'll need to run `git submodule update` if you're following along at home IIUC) and go from there.

Basically, what we need to do is add something to the `game-screen%` that will draw caverns. As a first test, how about just calculating the (scaled) Perlin noise for each point. If it's negative, it's open space. If it's positive, it's a wallRemember, Perlin noise has the range [-1.0, 1.0].

Here's what we'd need to add to `draw`; I put it just after the `clear`:

```scheme
; game-screen.rkt

; Draw some caverns around the player
(for* ([xi (in-range (send canvas get-width-in-characters))]
       [yi (in-range (send canvas get-height-in-characters))])
  (define x/y (recenter canvas (pt xi yi)))
  (when (> (perlin (* 0.1 (pt-x x/y)) (* 0.1 (pt-y x/y))) 0)
    (send canvas write #\# xi yi)))
```

If we run it, here's our first cave:

{{< figure src="/embeds/2013/initial-caverns.png" >}}

That's actually pretty awesome. There was about a 50/50 chance that we would have spawned inside of a wall or that we'd have basically all walls or all floor. But we have a nice mix and start in a neat little cutoff. One drawback that you can see if you're looking closely is that Perlin noise tends to have little artifacts. You can see that in the sharp edge both to the east and south of the player where the arguments to `perlin` cross over 0. How about we try `simplex` instead? Just switch `perlin` for `simplex` and you get this instead:

{{< figure src="/embeds/2013/with-simplex.png" >}}

That looks much nicer, but this time we did spawn in a wall, as you can see if you move a bit to one side:

{{< figure src="/embeds/2013/move-away.png" >}}

This actually reveals a pretty big downside with the current setup though. With the noise functions, we have an essentially unlimited cave system that we could wonder through. But it certainly doesn't look like it... Without scrolling, we can only see a small slice. So how about scrolling?

Well, first we want to abstract out the map generation. We're going to keep a cache of all of the tiles (so we can theoretically make the map mutable later if we want to--I'm imaging destructible terrain and burrowing baddies). There will be a {{< doc racket "hash" >}} of `(x y)` points to their contents. Even better, this would allow for additional systems of map generation on top of just noise. For example, we could add buildings or other more dungeon-y features just by pre-generating a second of coordinates. For now, this is just a symbol: either `wall` or `empty`. All together, we want to add this code to the `game-screen%`, right after we define the `player`:

```scheme
; game-screen.rkt

; Get the contents of a given point, caching for future use
; Hash on (x y) => char
(define caves (make-hash))
(define (get-tile x y)
  (unless (hash-has-key? caves (list x y))
    (hash-set! caves (list x y)
               (let ()
                 (define wall? (> (simplex (* 0.1 x) (* 0.1 y)) 0))
                 (cond
                   [wall? 'wall]
                   [else  'empty]))))
  (hash-ref caves (list x y)))
```

Then we change the drawing function to use `get-tile`:

```scheme
; game-screen.rkt

; Draw some caverns around the player
(for* ([xi (in-range (send canvas get-width-in-characters))]
       [yi (in-range (send canvas get-height-in-characters))])
  (define x/y (recenter canvas (pt xi yi)))
  (case (get-tile (pt-x x/y) (pt-y x/y))
    [(wall) (send canvas write #\# xi yi)]))
```

Run and we have exactly what we did before.

Next, scrolling. Basically, we have two options. We can either force the player to stay at the center of the screen and constantly scroll the world around him or we can only scroll when we're near the edge of the screen. For the moment, we're going to go with the first option since it's far simpler to code. Basically, we need to change two points in the code. Where previously we used `recenter` on the player coordinates, we'll just use (0 0). This way, we'll always draw the player at the center of the screen:

```scheme
; game-screen.rkt

; Draw the player centered on the screen
(let ([player (recenter canvas (pt 0 0))])
  (send canvas write #\@ (pt-x player) (pt-y player)))
```

Also, we want to offset the caves around the player. This is where the real beauty of using complex numbers as our coordinate system comes in. Since we can add them, we can add the player coordinates to the `x/y` of the tiles as we draw them. This will offset the map. It's really just as simple as tweaking this line:

```scheme
; game-screen.rkt
(define x/y (recenter canvas (+ (pt xi yi) player)))
```

With all of that, here's what we have:

{{< figure src="/embeds/2013/scrolling.png" >}}

I also added a debug printout to the top left showing the current player location. Note that the y-coordinate increases as you go down rather than up. Check out the <a href="https://github.com/jpverkamp/racket-roguelike/blob/master/src/game-screen.rkt" title="game screen source on GitHub">code on GitHub</a> if you're curious.

Unfortunately, we've run right into one of the downsides of using noise to generate maps. There's no real guarantee that things will be connected (in fact there's a pretty strong guarantee that they won't be). There are ways to deal with this, but in the interest of progress, I'm going to 'fix' it for the time being by hacking the player's initial coordinates to `(pt -12 -7)` which will give us a bit larger region to explore:

{{< figure src="/embeds/2013/start-at-neg12-neg7.png" >}}

There are two things that we still want to add today before we can consider the initial cave generation working: more cave features and collision detection.

More features are easy enough, we just need to modify the `get-tile` function to be able to add more things and `draw` to draw them. How about some water and trees. I'll use `(x z)` and `(y z)` instead of `(x y)` to generate these so there won't be any artifacts from using the same coordinates. Overall, here is the new core of the `get-tile` function:

```scheme
; game-screen.rkt
(define wall?  (> (simplex (* 0.1 x) (* 0.1 y) 0)         0.0))
(define water? (> (simplex (* 0.1 x) 0         (* 0.1 y)) 0.5))
(define tree?  (> (simplex 0         (* 0.1 x) (* 0.1 y)) 0.5))
(cond
  [wall?  'wall]
  [water? 'water]
  [tree?  'tree]
  [else   'empty])
```

This could certainly be tweaked. Here's the relevant part of the new drawing function:

```scheme
; game-screen.rkt
(case (get-tile (pt-x x/y) (pt-y x/y))
  [(wall) (send canvas write #\# xi yi)]
  [(water) (send canvas write #\space xi yi "blue" "blue")]
  [(tree) (send canvas write #\u0005 xi yi "green")]))
```

And here's what it looks like:

{{< figure src="/embeds/2013/water-and-trees.png" >}}

It's certainly not pretty, but I think it's a decent start. We'll make it better in a future post.

The last thing we want to do today is collision detection. Again, the idea should be straight forward. Essentially, we need to add a check in the `update` function that calls `get-tile` to see where we'll be going. If it's `empty`, move there. If not, block the move. Essentially, replace `update` with this:

```scheme
; game-screen.rkt

; Process keyboard events
(define/override (update key-event)
  ; NOTE: Y axis is top down, X axis is left to right

  ; Find where we are attempting to go
  (define target player)
  (case (send key-event get-key-code)
    [(numpad8 #\w up)    (set! target (+ (pt  0 -1) player))]
    [(numpad4 #\a left)  (set! target (+ (pt -1  0) player))]
    [(numpad2 #\s down)  (set! target (+ (pt  0  1) player))]
    [(numpad6 #\d right) (set! target (+ (pt  1  0) player))])

  ; Only move if it's open
  (when (eq? 'empty (get-tile (pt-x target) (pt-y target)))
    (set! player target))

  ; Keep the state
  this)
```

And now we can move around and collide with things.

Unfortunately, the collisions seem to be totally and completely random! Sometimes we can walk through walls; sometimes we collide with empty space. What in the world is going on?

Well, it turns out that I lied. Remember back when I said that all we had to do was add the `player` coordinate to the coordinate we were drawing? Well, that displays nicely. But it's not actually correct. What we actually wanted was this:

```scheme
; game-screen.rkt
(define x/y (recenter canvas (- player (pt xi yi))))
```

That solves one problem--now we correctly collide with terrain and can freely move through the empty space. But in solving one, we introduce another: we just flipped the coordinate system. Left is right and up is down! Madness!

But easy to fix madness. Just flip all of the differences in the `update` function:

```scheme
; game-screen.rkt
(case (send key-event get-key-code)
  [(numpad8 #\w up)    (set! target (+ (pt  0  1) player))]
  [(numpad4 #\a left)  (set! target (+ (pt  1  0) player))]
  [(numpad2 #\s down)  (set! target (+ (pt  0 -1) player))]
  [(numpad6 #\d right) (set! target (+ (pt -1  0) player))])
```

Now left is left, and up is up. All is good in the world...

Of course it's not. Now the coordinates are inverted. Moving east decreases the x-coordinate, as does south and the y-coordinate. The second seems strange, but remember that we wanted the y-coordinate to increase going down the screen (as computer graphics are wont to do).

For the time being, we're going to leave that as an exercise to the reader. I'm 90% sure I have a few things consistently flipped around, but at the moment I don't have the time to figure out exactly where. If anyone has a fix, feel free to post it in the comments. Otherwise, I'll fix it in the next post.

Now that we're done, if you'd like to see all of the code for this project, you can do so on GitHub:
- <a href="https://github.com/jpverkamp/racket-roguelike/tree/day-2" title="Racket Roguelike on GitHub">Racket Roguelike - Day 2</a>
- <a href="https://github.com/jpverkamp/racket-roguelike" title="Racket Roguelike on GitHub">Racket Roguelike - Up to date</a>

If you'd like to try it yourself, you'll need to have both <a href="http://git-scm.com/">Git</a> and <a href="http://racket-lang.org/">Racket</a> and run the following series of commands:

```bash
git clone git://github.com/jpverkamp/racket-roguelike.git
cd racket-roguelike
git checkout day-2
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
git checkout day-2
racket main.rkt
```

Like last time just remove the third line to get the up to date code instead if you'd rather.

For part 3, click here: [Racket Roguelike 3: Rats, rats, everywhere!]({{< ref "2013-04-18-racket-roguelike-3-rats-rats-everywhere.md" >}})



[^1]: Forever!
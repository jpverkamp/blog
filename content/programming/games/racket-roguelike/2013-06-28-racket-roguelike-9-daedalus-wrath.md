---
title: 'Racket Roguelike 9: Daedalus'' wrath!'
date: 2013-06-28 14:00:10
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
I think by now it's well past time that we got to adding a bit more content. So far, here's what we have (bolded entries we actually used in day 8):

* entities: **rat**, goblin, **bomb**, bomber goblin
* armor: **leather**, chain, plate, enchanted
* weapons: **club**, dagger, battle axe, longsword, magic sword
* potions: **health potion**
* coins: **copper**, silver, gold, platinum
* levels: **forest**, **caves**

We can do better than that though!

<!--more-->

Let's start with new levels.

First, let's try making something with a bit more structure. For both the forest and the caves, we have nice smooth flowing curves, let's go for some straight lines.

The basic idea is to use the same random number generators but at a different scale. We'll sample the points at every 10 or so tiles. If the sampled region is positive, include it. If not, don't. Sounds simple enough; here's some

First, check if we're in the 3 wide potential halls. We'll take the remainder for ten, if it's 4-6, use it.

```scheme
; Guaranteed wall if not x or y = 5 +- 1 (mod 10)
(define maybe-hall?
  (or (<= 4 (remainder (abs x) 10) 6)
      (<= 4 (remainder (abs y) 10) 6)))
```

We could have used 0, 1, and 9, but the math is just more complicated.

Next, we want to check if we have an empty space:

```scheme
; Find the endpoints
(define xlo (floor (/ x 10)))
(define ylo (floor (/ y 10)))

; Calculate if we'd have an open space
(define good-hall?
  (or (and (> (simplex (* 0.5 xlo)       (* 0.5 ylo)       seed) -0.25)
           (> (simplex (* 0.5 (+ xlo 1)) (* 0.5 ylo)       seed) -0.25))
      (and (> (simplex (* 0.5 xlo)       (* 0.5 ylo)       seed) -0.25)
           (> (simplex (* 0.5 xlo)       (* 0.5 (+ ylo 1)) seed) -0.25))))
```

I started with a multiplier at 0.1 and a threshold at 0, but that wasn't giving enough variation, so I increased the scale and lowered the threshold. This seems to give good results, so we'll go with it. Like all of the level generation parameters, it's easy enough though.

Finally, let's make stairs. We'll add an extra empty region around 0x0; otherwise, both tests will have to be positive:

```scheme
; Figure out which case we have
(cond
  ; Central section
  [(and (<= -3 x 3) (<= -3 y 3))
   (make-thing empty)]
  ; Guaranteed path
  [(and maybe-hall? good-hall?)
   (make-thing empty)]
  ; Wall
  [else
   (make-thing wall)])
```

But what about stairs? Everyone likes stairs!

First, let's restrict stairs more this time. We'll only put stairs in intersections that have already been generated and even then only in 1/10. How do we do that? First, restrict to the 5x5 points in each 10x10 grid:

```scheme
; Maybe a stairway if both are five
(define maybe-stairs?
  (= 5 (remainder (abs x) 10) (remainder (abs y) 10)))
```

Then swap out the middle section of the `cond`:

```scheme
; Guaranteed path
    [(and maybe-hall? good-hall?)
     ; Check for stairs
     (if (and maybe-stairs? (zero? (random 10)))
         (make-thing stairs-down)
         (make-thing empty))]
```

With this, we have a nice maze going on already. Here are a few examples. Start with a wide open world:

{{< figure src="/embeds/2013/1-Into-the-darkness.png" >}}

Move a bit and we already have a few nicely squared off choices:

{{< figure src="/embeds/2013/2-Two-choices.png" >}}

Go a bit further and now we have a full intersection:

{{< figure src="/embeds/2013/3-Intersection.png" >}}

Now we're starting to get blocked off:

{{< figure src="/embeds/2013/4-Blocked-off.png" >}}

And finally (after restarting), we find a stairway down:

{{< figure src="/embeds/2013/5-Going-down.png" >}}

Okay, that's all well and good. But what about inhabitants? We really need some critters to wonder around in here.

Say we wanted a Minotaur:

```scheme
(make-thing seeking-enemy
  [name "minotaur"]
  [character #\M]
  [color "brown"])
```

Yeah... that's pretty boring. Honestly, I'm not sure what sort of behavior to get them. If you have a good idea, drop a comment.

Better though, how about spiders. What I want is something that leaves behind a massive web. It turns out, between the `act` event on entities and the `on-enter` event on tiles, we have everything we need:

```scheme
(make-thing fleeing-enemy
  [name "spider"]
  [character #\s]
  [color "silver"]
  [(act me world)
   (define loc (thing-get me 'location))
   (define tile (send world tile-at (pt-x loc) (pt-y loc)))

   ; Try to move
   (thing-call seeking-enemy 'act me world)

   ; Check if we did (the old location is now empty)
   ; If so, make that tile a web that fades when walked on
   (when (null? (send world get-entities loc))
     (define old-tile (make-thing tile))

     (thing-set! tile 'character (integer->char 206))
     (thing-set! tile 'color "silver")
     (thing-set! tile 'solid #t)

     (thing-set! tile 'on-enter
       (lambda (entity world)
         (for ([key (in-list '(character color lighting walkable solid))])
           (thing-set! tile key (thing-get old-tile key))
           (thing-set! tile 'on-enter (lambda _ (void)))))))])
```

That's actually really neat. When the spider leaves a tile, it creates a web. When any entity enters that tile, it wipes it out. It could do all sorts of other things as well, like sticking the player in place, but this seems good for the moment.

So how does it look in practice? Well:

{{< figure src="/embeds/2013/6-Webs-everywhere.png" >}}

Personally, I think it looks pretty awesome. And you can walk through them just as expected. All on the first try as well.

Next week, we'll either add some more content or I'll try to add archery (and other usable items). Or perhaps in celebration of the 4th, we'll try for fireworks! We'll see how that goes.

As always, if you'd like to see all of the code for this project, you can do so on GitHub:
- <a title="Racket Roguelike on GitHub" href="https://github.com/jpverkamp/racket-roguelike/tree/day-9">Racket Roguelike - Day 9</a>
- <a title="Racket Roguelike on GitHub" href="https://github.com/jpverkamp/racket-roguelike">Racket Roguelike - Up to date</a>

If you'd like to try it yourself, you'll need to have both <a href="http://git-scm.com/">Git</a> and <a href="http://racket-lang.org/">Racket</a> and run the following series of commands:

```bash
git clone git://github.com/jpverkamp/racket-roguelike.git
cd racket-roguelike
git checkout day-9
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
git checkout day-9
racket main.rkt
```

For part 10, click here: [Racket Roguelike 10: Levels via automata!]({{< ref "2013-07-05-racket-roguelike-10-levels-via-automata.md" >}})



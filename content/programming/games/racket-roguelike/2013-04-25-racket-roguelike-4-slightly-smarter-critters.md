---
title: 'Racket Roguelike 4: Slightly smarter critters!'
date: 2013-04-25 14:00:44
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
A very minimal update today, since the many, many early May conference deadlines are fast approaching. But despite there only being a few lines of changes, already we are starting to get a bit more character to the game. Essentially, today we want to make the enemies smarter and add a bit more *explosive* sort of attacks.

<!--more-->

If you'd like to start at the beginning, click here: [Racket Roguelike 1: A GUI, screens, I/O, and you!]({{< ref "2013-04-04-racket-roguelike-1-a-gui-screens-i-o-and-you.md" >}})

First, we want a smarter type of enemy. Since we already have a unit hierarchy, all we have to do is extend wandering enemy. What we want is something that can figure out which direction the player is in and move towards them.

To do that, our points need to be a little smarter:

```scheme
; point.rkt

; Calculate the distance between two points
(define (distance p1 p2)
  (define (sqr n) (* n n))
  (sqrt (+ (sqr (- (pt-x p2) (pt-x p1)))
           (sqr (- (pt-y p2) (pt-y p1))))))

; Convert a point to a unit point (distance is one for origin)
(define (unit p)
  (define d (distance 0 p))
  (pt (/ (pt-x p) d)
      (/ (pt-y p) d)))
```

Essentially, we can use `unit` to take a vector (such as the one between an enemy and a player) and normalize it to a single unit. We can then round that to get a direction for movement from any of the eight directions. Something like this:

```scheme
; entities.rkt

; A seeking enemy runs towards the player (heedless of walls) 50% of the time
; The other 50% of the time they are identical to a wandering enemy
(define-thing seeking-enemy wandering-enemy
  [(act me world)
   (cond
     ; 50/50 of a seeking move
     [(= 0 (random 2))
      (define player-pt (thing-get (send world get-player) 'location))
      (define me-pt (thing-get me 'location))
      (define dir (unit (- player-pt me-pt)))
      (send world try-move
            me
            (+ me-pt
               (inexact->exact (round (pt-x dir)))
               (inexact->exact (round (pt-y dir)))))]
     ; Otherwise, wander
     [else
      (thing-call wandering-enemy 'act me world)])])
```

I could make it so that the enemy always seeks the player, but these seekers are pretty dumb. Given a single tile of walk on the shortest path between them, it will be stuck forever. But one thing that I've found with any sort of movement code is that a touch of pure randomness does a world of good. It tends to make things look a good deal smarter than they actually are. :smile:

On the flip side, we can use almost the exact same code to implement a `fleeing-enemy` just in the last part of the first `cond` block, subtract the direction from `me-pt` instead of adding it.

So how do these work in practice? Well, lets make the rats scared and a new class of enemies (goblins) that will run towards the player:

```scheme
; entities.rkt

; A list of random enemies that we can generate
(define random-enemies
  (vector
   (make-thing fleeing-enemy
     [name "rat"]
     [character #\r])
   (make-thing seeking-enemy
     [name "goblin"]
     [character #\g]
     [color "orange"]
     [attack 15]
     [defense 5])))
```

Sounds about time for a few screenshots.

First, here we have the original state of the game, with a few randomly generated rats and goblins all around.

{{< figure src="/embeds/2013/1-initial-state.png" >}}

Give it a few ticks and the goblins are already coming for us. How long do you think it will take them to cause some trouble?

{{< figure src="/embeds/2013/2-closer.png" >}}

Not so long... This is exactly the behavior that I was talking about. There's nothing in the code base right now to get the goblins to flank the player, but nevertheless they went right to it.

{{< figure src="/embeds/2013/3-ganging-up.png" >}}

And now, no more goblins. :smile: They're not so tough.

{{< figure src="/embeds/2013/4-no-more-goblins.png" >}}

Although I guess I am down to 60% of my original health...

So what about other enemies? Well, I did mention more interesting attacks. What would it take to make an enemy that explodes?

To really make it work, we need one more method in the `world%` class:

```scheme
; world.rkt

; Get a list of all entities by location
(define/public (get-entities p)
  (for/list ([entity (cons player npcs)]
             #:when (= p (thing-get entity 'location)))
    entity))
```

With that, we can write an `act` method which will calculate the distance to the player. If it's less than 1.5 (so technically we want {{< inline-latex "sqrt(2)" >}}, but 1.5 is close enough), explode. Anything within 1 tile will be attacked. Something like this:

```scheme
; entities.rkt

; An exploding enemy blows up whenever the player gets close to them
; Otherwise, they cannot move or attack (by default)
(define-thing exploding-enemy enemy
  [(act me world)
   (define distance-to-player
     (distance (thing-get (send world get-player) 'location)
               (thing-get me 'location)))
   (when (<= distance-to-player 1.5)
     ; Log message
     (send world log (format "~a explodes violently" (thing-get me 'name)))

     ; Damage neighbors
     (for* ([xd (in-range -1 2)]
            [yd (in-range -1 2)])
       (for ([other (send world get-entities
                           (+ (thing-get me 'location)
                              (pt xd yd)))])
         (unless (eqv? me other)
           (send world attack me other))))

     ; Destroy self
     (thing-set! me 'health -1))])
```

Use this to implement a bomb:

```scheme
; entities.rkt

(make-thing exploding-enemy
  [name "bomb"]
  [color "white"]
  [character #\O]
  [attack 50])
```

How does it look in practice?

Start by finding and approaching a bomb:

{{< figure src="/embeds/2013/5-on-approach.png" >}}

**BOOM!**

{{< figure src="/embeds/2013/6-boom.png" >}}

Ouch. Those things back a heck of a punch. (An attack of 50 will do that to do you.) Luckily, they don't chase after you. But what if they did?

```scheme
; entities.rkt

(make-thing seeking-enemy
  [name "bomber"]
  [character #\b]
  [color "orange"]
  [attack 25]
  [defense 5]
  [(act me world)
   (thing-call seeking-enemy 'act me world)
   (thing-call exploding-enemy 'act me world)])
```

The trick here is half-goblin, half-bomb. It will run right up to you and then explode. Looks like a lot of fun, doesn't it? It doesn't pack quite the same bunch, but it's still kind of terrifying. Particularly when you get something like this:

{{< figure src="/embeds/2013/7-incoming.png" >}}

A few rounds later:

{{< figure src="/embeds/2013/8-ouch.png" >}}

Boom! We'll still need to do a fair bit of balancing, these just don't do quite enough damage to really be scary. But it's certainly a start.

Well, that's all that I have for today. A bit of a short update, but we should have more next week as we get into the summer.

As always, if you'd like to see all of the code for this project, you can do so on GitHub:
- <a href="https://github.com/jpverkamp/racket-roguelike/tree/day-4" title="Racket Roguelike on GitHub">Racket Roguelike - Day 4</a>
- <a href="https://github.com/jpverkamp/racket-roguelike" title="Racket Roguelike on GitHub">Racket Roguelike - Up to date</a>

If you'd like to try it yourself, you'll need to have both <a href="http://git-scm.com/">Git</a> and <a href="http://racket-lang.org/">Racket</a> and run the following series of commands:

```bash
git clone git://github.com/jpverkamp/racket-roguelike.git
cd racket-roguelike
git checkout day-4
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
git checkout day-4
racket main.rkt
```

For part 5, click here: [Racket Roguelike 5: Armors and weapons and potions, oh my!]({{< ref "2013-05-02-racket-roguelike-5-armors-and-weapons-and-potions-oh-my.md" >}})



---
title: 'Racket Roguelike 5: Armors and weapons and potions, oh my!'
date: 2013-05-02 14:00:50
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
Another week, another step towards building a roguelike in Racket. This week, we're going to build another basic system (like the critters) that can easily be expanded with all sorts of crazy content: items and inventory.

<!--more-->

If you'd like to start at the beginning, click here: [Racket Roguelike 1: A GUI, screens, I/O, and you!]({{< ref "2013-04-04-racket-roguelike-1-a-gui-screens-i-o-and-you.md" >}})

This time around, let's start with the kinds of items that we want to support. As you may have guessed from the post title, we'll start with three: armor, weapons, and potions for boosted attack, defense, and temporary effects in turn.

First, we need a base `thing` on which we can base all of the rest of the items:

```scheme
; items.rkt

; All items have:
; - a display char/item if they're on the ground
; - if they're consumed or not (picked up)
; - methods for:
; -- being picked up
; -- being dropped
(define-thing item
  [character #\x]
  [color "white"]
  [consumable #f]
  [category 'unknown]
  [(on-pick-up item entity world)   (void)]
  [(on-drop item entity world) (void)])
```

First, we have the basic display features all of our items have. Then we have a flag that basically identifies if you can wear an item (`(not consumable)`) or if you consume it immediately (`consumable`).

Next, we have a category. Basically, our model will be that you can hold one item of each category at a given time. This way, you can have one kind of armor and one weapon and that's it. That will save us from having to make any sort of complicated inventory, although this same system could be adapted to a more flexible category to maximum count mapping.

Finally, we have two methods. I really do love functional programming when things like this come up. Basically (as should be obvious from the names), the first method will be called when them item is picked up (also when a consumable item is used), the second when it's dropped (never called for consumables).

So how does this work for an armor definition?

Well, we'll start with this:

```scheme
; items.rkt

; Armor protects the wearer
(define-thing armor item
  [character #\]]
  [defense 0]
  [category 'armor]
  [(on-pick-up item entity world)
   (thing-set! entity 'defense (+ (thing-get entity 'defense)
                                  (thing-get item 'defense)))]
  [(on-drop item entity world)
   (thing-set! entity 'defense (- (thing-get entity 'defense)
                                  (thing-get item 'defense)))])

(define *armors*
  (vector
   (make-thing armor [name "leather"]   [color "brown"]  [defense 1])
   (make-thing armor [name "chain"]     [color "gray"]   [defense 2])
   (make-thing armor [name "plate"]     [color "white"]  [defense 3])
   (make-thing armor [name "enchanted"] [color "purple"] [defense 5])))
```

Basically, we set the character, category, and behavior in a base thing. Then all the further definitions have to do is override the name, color, and specific value. The behavior will be copied over just fine.

Similarly, we can define weapons (the base definition is the same except using `'attack` instead of `'defense`):

```scheme
; items.rkt

(define *weapons*
  (vector
   (make-thing weapon [name "club"]        [color "brown"]  [attack 1])
   (make-thing weapon [name "dagger"]      [color "gray"]   [attack 2])
   (make-thing weapon [name "battle axe"]  [color "white"]  [attack 3])
   (make-thing weapon [name "longsword"]   [color "white"]  [attack 3])
   (make-thing weapon [name "magic sword"] [color "purple"] [attack 5])))
```

Finally, we have the actual consumables. Specifically, potions. Right now, there's really only one potion that makes sense, but the framework is more than flexible enough to do just about anything. Perhaps next week I'll start in on mutable terrain. :smile:

```scheme
; items.rkt

; Potions are single use and consumed on contact
(define-thing potion item
  [character #\!]
  [category 'potion]
  [consumable #t])

(define *potions*
  (vector
   (make-thing potion
     [name "health potion"]
     [color "red"]
     [(on-pick-up item entity world)
      (thing-set! entity 'health (+ 10 (thing-get entity 'health)))])))
```

Now all you have to do is walk over a potion and you'll feel much better.

So now we have a bunch of items, how do we tie them into the rest of the framework?

First, we need to be able to store them. Since we eventually want any entity (player or enemy) to hold an item, we'll add the inventory all of the way back at the base `entity` thing:

```scheme
; entities.rkt
(define-thing entity
  ...
  [inventory '()])
```

That will cascade through to all players and enemies.

Next, we need to do the same to tiles on the ground so that we can have items just lying about:

```scheme
; world.rkt
(define-thing tile
  ...
  [items '()])
```

Now, we have to actually generate some items lying around. Luckily, we can use almost exactly the same code that we used to generate the wandering monsters. Any time a tile is generated, there's a small chance of generating a random item as well.

```scheme
; world.rkt

; Sometimes even more rarely, generate some sort of treasure
(when (and (thing-get new-tile 'walkable)
           (< (random 1000) 1))
  (define new-item
    (let ([base (vector-choose-biased (vector-choose-random *all-items*))])
      (make-thing base)))

  (thing-set! new-tile 'items (cons new-item (thing-get new-tile 'items)))))
```

As we did with the new creatures and tiles, we wrap the items with a call to `make-thing`, making this item distinct from the base definition. Right now, there's no way to mutate items, but in the future we might want to have durability or some such--this will prevent all swords in the world from breaking when you swing any one of them.

So now we have items in the world, but we still can't see them. So we need to go over to the `game-screen` and modify the draw routine. Where previously the lowest layer was to draw the tile, now it will draw the tile if there's no item or the first item if there's at least one.

```scheme
; game-screen.rkt

(define tile (send world get-tile (pt-x x/y) (pt-y x/y)))
(cond
  [(null? (thing-get tile 'items '()))
   (send canvas write
         (thing-get tile 'character)
         xi
         yi
         (thing-get tile 'color))]
  [else
   (send canvas write
         (thing-get (car (thing-get tile 'items)) 'character)
         xi
         yi
         (thing-get (car (thing-get tile 'items)) 'color))]))
```

It's a bit ugly (so much duplicated code), but for the moment it will work.

Well, now that we're generating them, what does it actually look like?

{{< figure src="/embeds/2013/random-items.png" >}}

If you look to the left of the player, there's a nice gray `]` just sitting there. If I remember the definitions correctly, that's chain armor. If only we could actually pick it up...

(I made the screen a bit larger so we have room for the player inventory to print, which we'll get to shortly. It should still be reasonable on most people's screens.)

Well, for that, we can tie into the movement code. The only time that we could pick up an item is when we walk into it, so it has to be a walkable, unoccupied tile. We want to pick up any items we walk over, drop any items that have the category of one we just picked up, and directly consume and consumables. It's a bit of code, so let's just take a look first:

```scheme
; world.rkt

; If it's walkable and not occupied, update the location
; Also, pick up any items there, exchanging if types match
[(null? others)
 (thing-set! entity 'location target)

 (define (pick-up item)
   (thing-set! entity 'inventory (cons item (thing-get entity 'inventory)))
   (thing-set! tile 'items (remove item (thing-get tile 'items)))
   (thing-call item 'on-pick-up item entity this))

 (define (drop item)
   (thing-set! entity 'inventory (remove item (thing-get entity 'inventory)))
   (thing-set! tile 'items (cons item (thing-get tile 'items)))
   (thing-call item 'on-drop item entity this))

 (define (consume item)
   (thing-set! tile 'items (remove item (thing-get tile 'items)))
   (thing-call item 'on-pick-up item entity this))

 ; For each item on the ground
 (for ([item (in-list (thing-get tile 'items))])
   ; Remove same typed items from the inventory
   (for ([in-inv (in-list (thing-get entity 'inventory))]
         #:when (eq? (thing-get item 'category)
                     (thing-get in-inv 'category)))
     (drop in-inv))

   ; Pick up or consume the item
   (if (thing-get item 'consumable)
       (consume item)
       (pick-up item)))]
```

That should be relatively straight forward. And it actually works out great:

Here's another nice bit of chainmail just lying there for us.

{{< figure src="/embeds/2013/ooh-shiny.png" >}}

Walk right over it to put it on. You can see the armor we're currently wearing in the top left, along with the boost in defense we got (note: Things are totally unbalanced right now. That's a post all to itself.)

{{< figure src="/embeds/2013/invincible.png" >}}

Then we wander about a bit more. Hit a few bombs (those things **hurt**!). A bit of a pick-me-up would come in handy about now.

{{< figure src="/embeds/2013/think-i-need-that.png" >}}

Walk over it and drink it up:

{{< figure src="/embeds/2013/ahhh.png" >}}

Everything seems to be working well.

That's all we have today. I'm thinking about doing some line of sight calculations for next week (the screen is getting rather cluttered...). We'll see if I haven't changed my mind by then though. :smile:

As always, if you'd like to see all of the code for this project, you can do so on GitHub:
- <a href="https://github.com/jpverkamp/racket-roguelike/tree/day-5" title="Racket Roguelike on GitHub">Racket Roguelike - Day 5</a>
- <a href="https://github.com/jpverkamp/racket-roguelike" title="Racket Roguelike on GitHub">Racket Roguelike - Up to date</a>

If you'd like to try it yourself, you'll need to have both <a href="http://git-scm.com/">Git</a> and <a href="http://racket-lang.org/">Racket</a> and run the following series of commands:

```bash
git clone git://github.com/jpverkamp/racket-roguelike.git
cd racket-roguelike
git checkout day-5
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
git checkout day-5
racket main.rkt
```

For part 6, click here: [Racket Roguelike 6: Dig deeper!]({{< ref "2013-05-10-racket-roguelike-6-dig-deeper.md" >}})



---
title: 'Racket Roguelike 6: Dig deeper!'
date: 2013-05-10 14:00:24
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


> Moria... You fear to go into those mines. The dwarves delved too greedily and too deep. You know what they awoke in the darkness of Khazad-dum... shadow and flame.
> -- Saruman, Lord of the Rings

Today, we dig too deep.

<!--more-->

(If you'd like to start at the beginning, click here: [Racket Roguelike 1: A GUI, screens, I/O, and you!]({{< ref "2013-04-04-racket-roguelike-1-a-gui-screens-i-o-and-you.md" >}}))

Essentially, what we're going to do today is to tear out that placeholder we had for level generation and add a proper abstracted level generation script. With that, we might as well add the ability to generate a bunch of levels and just dig deeper and deeper.

Okay, so what's first? Well, the current code for level generation is in that huge, ugly `get-tile` function in `world.rkt`. Instead, let's make a new file: `levels.rkt`. This will have all of the level generation code. So what's first? Let's pull out the code generation:

```scheme
; levels.rkt

; Generate a simple cave with water and trees
(define (shallow-cave x y)
  (define wall?  (> (simplex (* 0.1 x) (* 0.1 y) 0)         0))
  (define water? (> (simplex (* 0.1 x) 0         (* 0.1 y)) 0.5))
  (define tree?  (> (simplex 0         (* 0.1 x) (* 0.1 y)) 0.5))
  (cond
    [wall?  (make-thing wall)]
    [water? (make-thing water)]
    [tree?  (make-thing tree)]
    [else   (make-thing empty)]))
```

This will represent the first few levels under the ground, with the same basic cave systems we've been using forever. There's on problem with that--it turns out that using the noise functions is both a time saver and will be our undoing. Since the function always returns the same values, given the same arguments, every level of our cave system will be identical. Not something we want (at least not for the caves).

The fix?

Add another parameter!

Technically, there are two ways that we could do this:

* Add a z-coordinate that corresponds to depth. This feels like some nice parallelism, but it means that every single time we play the game, the caves will be the same. Sub-optimal for a roguelike.
* Add a random seed that is set once per level. This will generate levels random (albeit consistently within a single playthrough), so this is the option we want.

This actually turns out to be really easy to implement:

```scheme
; levels.rkt

; Generate a simple cave with water and trees
(define (shallow-cave seed x y)
  (define wall?  (> (simplex (* 0.1 x) (* 0.1 y) seed)      0))
  (define water? (> (simplex (* 0.1 x) seed      (* 0.1 y)) 0.5))
  (define tree?  (> (simplex seed      (* 0.1 x) (* 0.1 y)) 0.5))
  (cond
    [wall?  (make-thing wall)]
    [water? (make-thing water)]
    [tree?  (make-thing tree)]
    [else   (make-thing empty)]))
```

Now we'll get all sorts of interesting levels. For example:

{{< figure src="/embeds/2013/cave-1.png" >}}

{{< figure src="/embeds/2013/cave-2.png" >}}

(Yes, there are only rats and basic gear. I'll get to that in a second.)

So we can make caves, just like we always have, but what about other sorts of terrain? Well, all we have to do is copy/paste/tweak. Let's say instead of caves and walls, we want grassland (but still with trees and small ponds). We'd get something like this:

```scheme
; levels.rkt

(define-thing grass tile
  [character #\.]
  [color "green"]
  [walkable #t])

; The surface level with grass, water, and trees
(define (surface seed x y)
  (define water? (> (simplex (* 0.1 x) seed      (* 0.1 y)) 0.5))
  (define tree?  (> (simplex seed      (* 0.1 x) (* 0.1 y)) 0.5))
  (cond
    [water? (make-thing water)]
    [tree?  (make-thing tree)]
    [else   (make-thing grass)]))
```

{{< figure src="/embeds/2013/grassland.png" >}}

We can easily tune this to make any sorts of levels. Even better, we don't necessary need to use the noise functions. We could theoretically make levels based on something like [[wiki:cellular automaton]]() or even scripted levels (perhaps loaded from external files?). All we have to do is be able to generate a specific tile when asked and our framework will generate the rest. Speaking of which, how do we tie this into the previous `get-tile` function?

Well, we need a bit of abstraction first. First, how do we want to represent z-levels? Theoretically, we could use the same hash that we've been using, only using `(list x y z)` instead of `(list x y)`. But keeping all of that in one hash seems like a recipe for trouble, so instead, we'll store a hash of hashes. Each outer hash will be indexed by depth, the inner by the point. Then we can have a local variable referring to just the current level.

While we're at it, let's all refactor some other code. We need to store the `seed` that I mentioned earlier for each level. In addition, we want to store the generation functions for tiles (and later NPCs and items). Finally, so we don't have an ever-growing list of NPCs all acting each tick, let's move the NPC lists into the level. In the end, something like this:

```scheme
; levels.rkt

; Level defintions
; tile-gen : x y -> tile
; npc-gen  : x y -> npc or #f
; item-gen : x y -> item or #f
(define-struct level-definition (tile-gen npc-gen item-gen))

; All levels
; (pt x y) : tile
; 'npcs    : list of npcs
; 'gen     ; level definition (see above)
; 'seed    ; a random seed [0,1) generated once per level
(define levels (make-hasheq))
(define current-depth (make-parameter 0))

; Generate a new level (if it doesn't already exist)
(define (get-level depth)
  (unless (hash-has-key? levels depth)
    (define level (make-hash))
    (hash-set! level 'seed (random))
    (hash-set! level 'npcs '())
    (hash-set! level 'gen
      (cond
        [(= depth 0)
         (level-definition surface nothing nothing)]
        [else
         (level-definition shallow-cave rats-only base-items)]))
    (hash-set! levels depth level))
  (hash-ref levels depth))
```

With this, `get-level` mirrors `get-tile`. If a level doesn't currently exist, it will generate a new one. In this case, we have our two generation functions. If the level is 0 (the ground level), use the grassland generator. If it's less than that, for now always generate caves. There are a few other generators (`nothing`, `rats-only`, and `base-items`) but I'll get to those in a moment. (You can get a pretty good hint for what those will be by looking at the `level-definition` struct.)

With this, we have what we need to rebuild the `get-tile` function:

```scheme
; levels.rkt

; Fetch a tile
(define (get-tile x y)
  (define current-level (get-level (current-depth)))
  (define seed (hash-ref current-level 'seed))

  ; If the tile doesn't already exist, generate it
  (unless (hash-has-key? current-level (pt x y))
    ; Get the new tile
    (define new-tile ((level-definition-tile-gen (hash-ref current-level 'gen)) seed x y))
    (hash-set! current-level (pt x y) new-tile)

    ; NPCs and items are only on walkable tiles
    (when (thing-get new-tile 'walkable)
      ; (Potentially) generate a new npc
      (define new-npc ((level-definition-npc-gen (hash-ref current-level 'gen)) seed x y))
      (when (and (not (void? new-npc)) new-npc)
        (let ([new-npc (make-thing new-npc [location (pt x y)])])
          (hash-set! current-level 'npcs (cons new-npc (hash-ref current-level 'npcs)))))

      ; (Potentially) generate a new item for that tile
      ; Do not generate an item if there already is one (generated by the tile generation routine)
      (when (null? (thing-get new-tile 'items '()))
        (define new-item ((level-definition-item-gen (hash-ref current-level 'gen)) seed x y))
        (when (and (not (void? new-item)) new-item)
          (let ([new-item (make-thing new-item)])
            (thing-set! new-tile 'items (cons new-item (thing-get new-tile 'items))))))))

  ; Return the tile (newly generated or not)
  (hash-ref current-level (pt x y)))
```

It has the same structure it always did, but now it's nicely abstracted. The first chunk just generates a tile using the generation functions we defined earlier (`surface` and `shallow-caves`). The code to do that `((level-definition-tile-gen (hash-ref current-level 'gen)) seed x y)` is a bit ugly, but it works well enough.

After that (if and only if we have a `walkable` tile), try to generate an NPC. The NPC generation functions are going to look exactly like the tile functions, except the return entities rather than tiles and can return either `void` or `#f` if there's no NPC in that location. So if we just want an empty world, we can always return `#f`:

```scheme
; levels.rkt

; No NPCs (also works for items)
(define (nothing seed x y) #f)
```

If we want a world full of rats (roughly 1% of the time):

```scheme
; levels.rkt

; Look up a thing from a vector by 'name
(define (lookup vec name)
  (let/ec return
    (for ([thing vec]
          #:when (equal? name (thing-get thing 'name #f)))
      (return thing))
    (return #f)))

; Rats. All of the rats.
(define (rats-only seed x y)
  (when (zero? (random 100))
    (lookup *entities* "rat")))
```

The lookup function is so I can reuse those vectors of things I've been defining in `entities.rkt` and `items.rkt`. Basically, it finds the first `thing` with the given `'name` field.

Items work much the same way. If we want just the basic tier of items, we can do this:

```scheme
; levels.rkt

; Only basic items
(define (base-items seed x y)
  (when (zero? (random 100))
    (case (random 4)
      [(0) (lookup *armors* "leather")]
      [(1) (lookup *weapons* "club")]
      [(2) (lookup *potions* "health potion")]
      [(3) (lookup *coins* "copper coin")])))
```

(I added a new kind of item: `stackable`. Rather than replacing other items of a given type, they stack with them, combining quantities. Coins are currently the only stackable and at the moment, they're completely worthless. But it's a neat proof of concept. Check out the code <a title="Racket Roguelike on GitHub" href="https://github.com/jpverkamp/racket-roguelike">on GitHub</a> for more details.)

Okay. That's basically everything to actually generate the levels. But we still have two fairly big problems:

* How does this hook up to the code we already have?
* How do we get to different levels?

For the first problem, we need to tweak `world.rkt`. Essentially, we renamed the `get-tile` function as `tile-at` and just wrapped `get-tile` from `levels.rkt`. Likewise with `update` and `update-npcs`. It's pretty straight forward, check out the code <a title="Racket Roguelike on GitHub" href="https://github.com/jpverkamp/racket-roguelike">on GitHub</a> for more details.

The more interesting challenge is getting to different levels. The traditional way to do that in roguelikes is stairs. So we need a new tile type. But right now, we don't have a way to attach events to tiles. So we'll do both at once. Now, any tile can have an (optional) `on-enter` event, much like the `on-pickup` and `on-drop` events on items. Something like this:

```scheme
; levels.rkt

(define-thing stairs-up tile
  [character #\<]
  [color "gold"]
  [walkable #t]
  [(on-enter entity world)
   (when (eq? (send world get-player) entity)
     (ascend)
     (hash-set! (get-level (current-depth))
                (thing-get (send world get-player) 'location)
                (make-thing stairs-up)))])
```

`stairs-up` will be much the same. Essentially, when the player enters a tile (the `when` keeps those pesky rats from using the stairs for the time being), they will call `ascend` which just sets the `current-depth` variable we defined earlier to one higher, which is all we would need, since the next rendering step will call `get-tile` which in turn calls `get-level`. Since there is no level yet (unless we leave the level and come back), a new one will be generated. That's the beauty of the lazy tile generation setup we're using.

The final chunk is particularly amusing. Basically, when you code up the stairs, it will generate the matching stairs on the next level. This isn't perfect, since if you go back to a level you've already been on, the stairs will appear from nowhere. For now, we'll consider this a 'feature'. Hidden stairs. :smile: Another problem is that there's nothing stopping the stairs from popping up in the middle of a wall. Since stairs on only triggered by entering them, that will be game over. Clearly sub-optmimal, but that's something we can save for later.

Speaking of which, how do we implement `on-enter`? Well, that's where the `try-move` function in `world.rkt` comes in. Find the one place where the player can move (where the target is `walkable` and not otherwise occupied) and add this code:

```scheme
; world.rkt

; Look for an on-enter item
(define on-enter (thing-get tile 'on-enter #f))
(when on-enter
  (on-enter entity this))
```

And that's all we need. Bam, z-levels. And it should be really easy to add more level definitions with all sorts of varied properties. One of these weeks (soon probably), I should actually work on balancing and adding a bunch of new content. That will be the last step for making a full game. But really, we're basically there. All we really need still to have a game is more content and a way to win (It's perfectly possible to lose right now, but winning? Not so much).

Before we go, how about a few more screenshots with stairs and all?

{{< figure src="/embeds/2013/1-all-peaceful.png" >}}

Starting out, we're in a nice peaceful field. All we really have to do is find some stairs (or wander off into infinity (and beyond!)).

{{< figure src="/embeds/2013/2-going-down.png" >}}

Found some stairs. Down we go!

{{< figure src="/embeds/2013/3-into-the-caves.png" >}}

A nice little cavern. There are rats south and east and one of those nice new coins up north.

{{< figure src="/embeds/2013/4-got-a-coin-killed-a-rat.png" >}}

Here we've grabbed the coin up north and killed the rat over by the potion. The coins have values based on the "gold standard" (1 gold = 10 silver = 100 copper, yay D&amp;D!), so it's really not much. But since they don't do anything anyways, it's as good as gold!

Let's try heading back up. Remember that other set of stairs? What happens if we take those?

{{< figure src="/embeds/2013/5-up-down-wall.png" >}}

Oops. Yeah, I really should fix that. Now I'm in the middle of a wall and thus stuck. I really should add a way to manually trigger `on-enter` actions. We'll see how that goes.

Well, that's it for today. It's really starting to look like a game now. :smile:

As always, if you'd like to see all of the code for this project, you can do so on GitHub:
- <a title="Racket Roguelike on GitHub" href="https://github.com/jpverkamp/racket-roguelike/tree/day-6">Racket Roguelike - Day 6</a>
- <a title="Racket Roguelike on GitHub" href="https://github.com/jpverkamp/racket-roguelike">Racket Roguelike - Up to date</a>

If you'd like to try it yourself, you'll need to have both <a href="http://git-scm.com/">Git</a> and <a href="http://racket-lang.org/">Racket</a> and run the following series of commands:

```bash
git clone git://github.com/jpverkamp/racket-roguelike.git
cd racket-roguelike
git checkout day-6
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
git checkout day-6
racket main.rkt
```

(Note: Sorry I'm a day late this week. Life's been crazy between conference deadlines and getting married. One of these days I'll actually actually write one of these posts ahead of time... Or not.)

For part 7, click here: [Racket Roguelike 7: Into Darkness!]({{< ref "2013-05-17-racket-roguelike-7-into-darkness.md" >}})



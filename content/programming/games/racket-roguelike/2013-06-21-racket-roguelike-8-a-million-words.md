---
title: 'Racket Roguelike 8: A million words!'
date: 2013-06-21 14:00:24
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
If a picture is worth a thousand words, surely an animated GIF is worth a few more than that. :smile:

<!--more-->

{{< figure src="/embeds/2013/boom.gif" >}}

The short version: I finally figure out how to animation! It's terribly hacky--abusing both mutation on the module level and the Racket GUI event queue--and I really would love to know how to do it better. But for the moment, it works, which means that I can move forward with generating more content and weapons using the framework in future weeks.

So how does it work?

Well, the problem that I had the first few times around all revolved around the Racket GUI event queue not allowing me (rightfully so) to update the GUI while it was still processing. So I had to add in events to draw things. {{< doc racket "queue-callback" >}} to the rescue! It's a neat little function that lets you add an arbitrary thunk to the event queue. But I didn't want to make a content generator deal with that directly, so we need an API.

```scheme
; animate.rkt

(provide animate! set-animate!)

(define (animate! . thunks)
  (void))

(define (set-animate! f)
  (set! animate! f))
```

The first function will be what we call. The second is the ugliness that I was talking about earlier. Because we want access to the drawing functions, we need to have access to the scope in `gui.rkt`, but we want to be able to use `animate!` in any other file. Normally, that would get us circular imports.

So it's ugly. So it goes. What do we end up setting `animate!` to?

```scheme
; gui.rkt

; Correctly set the animation function
(set-animate!
 (lambda thunks
   (for-each (lambda (thunk) (thunk)) thunks)
   (send active-screen draw canvas)
   (send frame refresh)
   (yield)))
```

The first bits are easy enough, we take any number of thunks and then evaluate each of them in turn. Then we have the normal drawing functions. The only new part is the {{< doc racket "yield" >}} function which sends control back to the event queue. I'm not entirely sure it's necessary, but the original code didn't work and with `yield` it does.

With that, now we can animate things. There are a few caveats to keep in mind:

* Any code you want to run, you have to wrap in thunks. Otherwise it would be evaluated once, at launch.
* Any changes to the GUI each have to be in their own `animate!` block, since the screen is only redrawn once per draw.
* The code will run as quickly as possible, so you'll often want to put in a call to `sleep` to actually make changes visible.

So let's take an example in practice (the one in the GIF above): the bomb.

All of this code will go into the act function in exploding-entity, adding to the previous damage code that was already there.

```scheme
; entities.rkt

; An exploding enemy blows up whenever the player gets close to them
; Otherwise, they cannot move or attack (by default)
(define-thing exploding-enemy enemy
  [(act me world)
   ...

   ; Get the neighboring tiles
   (define neighbors
     (for*/list ([xd (in-range -1 2)]
                 [yd (in-range -1 2)])
       (define loc (+ (thing-get me 'location) (pt xd yd)))
       (send world tile-at (pt-x loc) (pt-y loc))))

   ; Store the original color
   (for ([tile (in-list neighbors)])
     (thing-set! tile 'original-color (thing-get tile 'color))
     (thing-set! tile 'original-character (thing-get tile 'character))
     (thing-set! tile 'character #\*))

   ; Animate through several colors
   (define (random-color) (vector-ref (vector "red" "yellow" "white") (random 3)))
   (for ([i (in-range 10)])
     (animate!
      (lambda ()
        (for ([tile (in-list neighbors)])
          (thing-set! tile 'color (random-color))
          (sleep 1)))))

   ; Clear them
   (animate!
    (lambda ()
      (for ([tile (in-list neighbors)])
        (thing-set! tile 'color (thing-get tile 'original-color))
        (thing-set! tile 'character (thing-get tile 'original-character)))))

   ...
```

And that's it. Originally, I was storing the colors in the enclosing scope, but then I realized that the `thing` framework allows attaching arbitrary fields at runtime. So I could just store the original color as needed and then restore it. Just so long as no one else decides to mess with it mid-explosion, it should work just fine.

And that's actually it for this week. It's a short post and rather little final code, but it took more than a little while to get entirely correct. I'm still not thrilled with the hacks it took to get it to work, but it's a start. Perchance next week I'll take the time to actually add a bit more content. :smile:

As always, if you'd like to see all of the code for this project, you can do so on GitHub:
- <a title="Racket Roguelike on GitHub" href="https://github.com/jpverkamp/racket-roguelike/tree/day-8">Racket Roguelike - Day 8</a>
- <a title="Racket Roguelike on GitHub" href="https://github.com/jpverkamp/racket-roguelike">Racket Roguelike - Up to date</a>

If you'd like to try it yourself, you'll need to have both <a href="http://git-scm.com/">Git</a> and <a href="http://racket-lang.org/">Racket</a> and run the following series of commands:

```bash
git clone git://github.com/jpverkamp/racket-roguelike.git
cd racket-roguelike
git checkout day-8
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
git checkout day-8
racket main.rkt
```

For part 9, click here: [Racket Roguelike 9: Daedalus' wrath!]({{< ref "2013-06-28-racket-roguelike-9-daedalus-wrath.md" >}})



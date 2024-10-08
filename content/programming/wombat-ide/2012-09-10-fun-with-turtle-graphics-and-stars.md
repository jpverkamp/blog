---
title: Fun with turtle graphics and stars
date: 2012-09-10 14:00:15
programming/languages:
- Java
- Scheme
programming/topics:
- Fractals
---
After [Saturday's post]({{< ref "2012-09-08-the-first-two-problems.md" >}}) on using [turtle graphics]({{< ref "2012-04-13-wombat-ide-turtle-graphics.md" >}}) to draw letters, I wanted to get back into drawing some [[wiki:fractals]](). Fractals are cool.

<!--more-->

In particular, there's this one fractal that I always used to draw in middle/high school by hand. It got a little complicated after a few iterations, but it was a good way to keep my hands busy during class. Anyways, without further ado, here's what I'm trying to generate:

{{< figure src="/embeds/2012/star.png" >}}

Sort of a combination star/snowflake/spirally thing. In any case, it turns out the code to draw it isn't actually that terribly complicated:

```scheme
(define (draw-star! t d n)
  (let loop ([d d] [n n] [skip 5])
    (set-pen-color! t (color (random 256) (random 256) (random 256)))
    (when (> n 0)
      (turn-to! t 0)
      (repeat 4
        (turn! t 90)
        (when (not (= (mod skip 360) (mod (turtle-direction t) 360)))
          (block t
            (move! t d)
            (let* ([d2 (* 0.5 (sqrt 2) d)])
              (block t
                (turn-and-move! t -135 d2)
                (turn-and-move! t -90 d2)
                (move-and-turn! t (- d2) 45)
                (let loop ([i 10] [d3 (* 0.5 (sqrt 2) d2)])
                  (when (> i 0)
                    (move-and-turn! t d3 -45)
                    (loop (- i 1) (* 0.5 (sqrt 2) d3))))))
            (loop (/ d 2) (- n 1) (+ 180 (turtle-direction t)))))))))
```

Perhaps the most interesting bit is the variable `skip`. The goal is that when you expand out in a direction, you only recursively expand in the three directions other than the one you came from. If you take out the `skip` code, you get something more like this:

{{< figure src="/embeds/2012/star-no-skip.png" >}}

Still neat, but not what I was going for. As a side note, I started with `(= skip 5)` basically because none of the branches are going to be at 5 degrees. Originally, I started with `skip` as `#f`, but that didn't work so well with `=`. So it goes.

I used a few helper functions to shorten the turn/move blocks, but they're obvious enough (I'm actually considering adding them to the API though):

```scheme
(define (turn-and-move! t turn move)
  (turn! t turn)
  (move! t move))

(define (move-and-turn! t move turn)
  (move! t move)
  (turn! t turn))
```

To draw it, this is all you need:

```scheme
(let ([turtle (hatch)])
  (draw-star! turtle 100 4)
  (draw-turtle turtle))
```

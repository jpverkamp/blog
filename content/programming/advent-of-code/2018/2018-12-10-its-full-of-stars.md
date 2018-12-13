---
title: "AoC 2018 Day 10: It's Full of Stars!"
date: 2018-12-10
programming/languages:
- Racket
programming/sources:
- Advent of Code
series:
- Advent of Code 2018
---
### Source: [The Stars Align](https://adventofcode.com/2018/day/10)

> **Part 1:** Given a system of moving particles (with position and velocity) find the point where the particles spell a message. What is that message?

<!--more-->

First, load the particles:

```racket
(struct particle (px py vx vy) #:transparent)

(define (particle-update p [steps 1])
  (match-define (particle px py vx vy) p)
  (particle (+ px (* steps vx)) (+ py (* steps vy)) vx vy))

(define (read-particle [in (current-input-port)])
  (define line (read-line))
  (cond
    [(eof-object? line) line]
    [else
     (match-define
       (regexp #px"position=<\\s*(-?\\d+),\\s*(-?\\d+)> velocity=<\\s*(-?\\d+),\\s*(-?\\d+)>"
               (list _ px py vx vy))
       line)
     (particle (string->number px)
               (string->number py)
               (string->number vx)
               (string->number vy))]))

(define INITIAL-PARTICLES
  (port->list read-particle))
```

Next, since the particles are always moving at a constant speed, it's likely that the message will appear either at or very near to the point where they are the closest together. So let's find the current bounding box of all the particles and the volume of that box:

```racket
; Get the bounds at a given tick
(define (bounds tick)
  (define particles (map (curryr particle-update tick) INITIAL-PARTICLES))
  (for/fold ([min-x +inf.0] [max-x -inf.0] [min-y +inf.0] [max-y -inf.0])
            ([p (in-list particles)])
    (match-define (particle px py vx vy) p)
    (values (min min-x px) (max max-x px) (min min-y py) (max max-y py))))

; Get the volume at a given tick
(define (volume tick)
  (define-values (min-x max-x min-y max-y) (bounds tick))
  (* (- max-x min-x)
     (- max-y min-y)))
```

Then we can find when that volume is the smallest:

```racket
; Find the tick where volume hits a minimum
(define (min-volume)
  (let loop ([v (volume 0)]
             [tick 1])
    (define v^ (volume tick))
    (cond
      [(> v^ v) (sub1 tick)]
      [else
       (loop v^ (add1 tick))])))
```

Okay, so we can find out when the message is. What about where. Let's render the particles as an image:

```racket
; Render a given ticket as an image
(define (render tick)
  (define particles (map (curryr particle-update tick) INITIAL-PARTICLES))
  (define-values (min-x max-x min-y max-y) (bounds tick))
  (flomap->bitmap
   (build-flomap*
    1
    (exact-round (+ 10 (- max-x min-x)))
    (exact-round (+ 10 (- max-y min-y)))
    (λ (x y)
      (cond
        [(for/first ([p (in-list particles)]
                     #:when (and (= x (- (particle-px p) min-x -5))
                                 (= y (- (particle-py p) min-y -5))))
           p)
         (vector 1.0)]
        [else
         (vector 0.0)])))))
```

There's a bit of extra space around the image just because I found some letters hard to read without a border. It's really not necessary to solve the puzzle.

That doesn't work at all well for the initial particles (the image is huge), but if you render just a range around the minimum:

```racket
; Find the minimum volume and render a few frames around that
(define minimum-tick (min-volume))
(printf "minimum volume at: ~a\n" minimum-tick)

(for ([i (in-range (- minimum-tick 10) (+ minimum-tick 11))])
  (printf "rendering ~a\n" i)
  (send (render i)
        save-file
        (format "frame-~a.png" (~a i #:min-width 4 #:align 'right #:left-pad-string "0"))
        'png))
```

Let's see it in action:

```bash
$ cat input.txt | racket particle-animator.rkt

minimum volume at: 10159
rendering 10149
rendering 10151
...
rendering 10159
...
rendering 10168
rendering 10169

$ open frame-10159.png
```

{{< figure src="/embeds/2018/aoc-10-frame-10159.png" >}}

That's fun. Since we already have all the frames, lets animate them!

```bash
$ identify frame-*

frame-10149.png PNG 168x119 168x119+0+0 8-bit sRGB 1.54KB 0.000u 0:00.000
frame-10150.png PNG 158x109 158x109+0+0 8-bit sRGB 1.42KB 0.000u 0:00.000
...
frame-10159.png PNG 71x19 71x19+0+0 8-bit sRGB 257B 0.000u 0:00.000
...
frame-10168.png PNG 160x109 160x109+0+0 8-bit sRGB 1.4KB 0.000u 0:00.000
frame-10169.png PNG 170x119 170x119+0+0 8-bit sRGB 1.52KB 0.000u 0:00.000

$ convert frame-*.png -background black -gravity center -extent 180x129 aoc-10-animaged.gif
```

{{< figure src="/embeds/2018/aoc-10-animated.gif" >}}

Whee!

> **Part 2:** When does the message appear?

Another weird part 2. We already know this.

```bash
$ cat input.txt | racket particle-animator.rkt

minimum volume at: 10159
...
```

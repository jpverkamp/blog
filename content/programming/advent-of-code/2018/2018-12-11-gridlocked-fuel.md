---
title: "AoC 2018 Day 11: Gridlocked Fuel"
date: 2018-12-11
programming/languages:
- Racket
programming/sources:
- Advent of Code
series:
- Advent of Code 2018
---
### Source: [Chronal Charge](https://adventofcode.com/2018/day/11)

> **Part 1:** Define a grid as follows (x,y coordinates + a constant C):

> - {{< inline-latex "r(x) = x + 10" >}}
> - {{< inline-latex "G(x, y) = hundreds(r(x) * (r(x) * y + C)) - 5" >}}

> Find the 3x3 area in a 300x300 grid with the highest total {{< inline-latex "G(x, y)" >}}.

<!--more-->

Weird. The fuel function in racket:

```racket
; Calculate the fuel at a point
(define (fuel x y)
  (- (quotient (remainder (* (+ (* (+ x 10) y) (serial)) (+ x 10)) 1000) 100) 5))
```

I'm curious, so let's render my fuel map:

```racket
; Render a fuel map
(define (render-fuel)
  (flomap->bitmap
   (build-flomap*
    1 300 300
    (λ (x y)
      (vector (/ (+ 5 (fuel x y)) 10))))))
```

{{< figure src="/embeds/2018/aoc-11-fuel.png" >}}

It's pretty I guess.

So what's the maximum of a 3x3 area?

```racket
; Calculate total fuel at a 3x3 point (from top left)
(define (fuel-3x3 x y)
  (for*/sum ([xd (in-range 3)]
             [yd (in-range 3)])
    (fuel (+ x xd) (+ y yd))))

; Part 1, maximum fuel on a 3x3 grid
(let ()
  (define-values (x y f)
    (for*/fold ([max-x 0] [max-y 0] [max-fuel (fuel-3x3 0 0)])
               ([x (in-range 298)]
                [y (in-range 298)]
                [f (in-value (fuel-3x3 x y))]
                #:when (> f max-fuel))
      (values x y f)))

  (printf "[part1] ~a,~a has ~a fuel\n" x y f))
```

That works.

```bash
$ racket magical-fuelinator.rkt --serial 9810

[part1] 245,14 has 29 fuel
```

> **Part 2:** What is the maximum fuel when the grid can be any size (1-300)?

There's probably a better way to do this, but let's just brute force it:

```racket
; Calculate total fuel at any size square (from top left)
(define (fuel-square x y [size 3])
  (for*/sum ([xd (in-range size)]
             [yd (in-range size)])
    (fuel (+ x xd) (+ y yd))))

; Part 2: Find maximum fuel at any size
(let ()
  (define-values (x y s f)
    (for*/fold ([max-x 0] [max-y 0] [max-s 1] [max-fuel (fuel-square 0 0 1)])
               ([s (in-range 1 300)]
                [x (in-range (- 301 s))]
                [y (in-range (- 301 s))]
                [f (in-value (fuel-square x y s))]
                #:when (> f max-fuel))
      (values x y s f)))

  (printf "~a,~a (size: ~a) has ~a fuel\n" x y s f))
```

That's slow. But it works:

```bash
$ racket magical-fuelinator.rkt --serial 9810

[part1] 245,14 has 29 fuel
[part2] 235,206 (size: 13) has 109 fuel
```

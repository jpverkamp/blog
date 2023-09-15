---
title: Langton's ant
date: 2014-08-07
programming/languages:
- Racket
- Scheme
programming/sources:
- Daily Programmer
programming/topics:
- Algorithms
- Cellular Automata
- Procedural Content
---

Here's another post from /r/DailyProgrammer: [Advanced Langton's Ant](http://www.reddit.com/r/dailyprogrammer/comments/2c4ka3/7302014_challenge_173_intermediate_advanced/). I'm a bit behind the times (see tomorrow's post), but it's still an interesting enough exercise, so let's go for it!

{{< figure src="/embeds/2014/LR.gif" >}}

<!--more-->

First, let's define the problem. From Wikipedia: [[wiki:Langton's ant]]()

> Squares on a plane are colored variously either black or white. We arbitrarily identify one square as the "ant". The ant can travel in any of the four cardinal directions at each step it takes. The ant moves according to the rules below:

> * At a white square, turn 90° right, flip the color of the square, move forward one unit
> * At a black square, turn 90° left, flip the color of the square, move forward one unit

That's actually pretty simple sounding, so let's just go ahead and jump into generalizing. Instead of only two states (`white` and `black`), let's generalize to an arbitrary number of states. Instead of flipping when the ant visits the state, instead advance to the next. That way, we can define ants quite simply:


* `LR` - an ant that turns left on state 1 to 2 and right on state 2 to 1 (the simple ant described above)
* `LL` - an ant that always turns left; this one is boring, it just runs in circles
* `LRRL` - a more complicated ant that turns left on either 1 to 2 or 4 to 1, but turns right on 2 to 3 or 3 to 4[^1]


Okay, fair enough. We also want to decide right now that we're going to support arbitrarily large grids. It would be a lot easier to define a certain region, since then we can use something like a 2-dimensional array to store the current states, but it's not actually any harder to support an unlimited grid. What we need is a way of associating a location with a state. Sounds like a job for a hash!

Except we need two points for a location. So we can either have nested hashes, or we can use a trick that I've used a time or two before: representings points as complex numbers. In this way, the point `(0, 0)` is the number `0+0i`; `(3, -7)` is `3-7i`. So long as we keep the numbers {{< doc racket "exact" >}}, we should be able to use it as a hash key without issue.

Okay, so what do we need to represent the current state of a Langton's Ant simulation? We need the grid, that's true. But we also need the ant. More specifically, we need a location and current facing (since we need a direction to turn left/right from). Also, we'll need to store the current rule. We could keep this out of the structure, but since it's essentially the core of what we need to do, we'll put it in the {{< doc racket "struct" >}}.

Something like this:

```scheme
(struct ant (rule location direction grid) #:transparent)
(define (make-ant rule) (ant rule 0 0+i (hash)))
```

Okay, the rule is straight forward enough. Just a string of `L` or `R` characters. Location is a little stranger, but just remember that it's an exact complex number. So `0` is `0+0i` is `(0, 0)`. Direction takes some doing. Luckily though, it's going to make our math amazingly easy. Essentially, we're going to use complex multiplication. Taking from the Wikipedia page on [[wiki:rotation|Rotation (mathematics)]]():

> Points on the {{< inline-latex "R^2" >}} plane can be also presented as complex numbers: the point `(x, y)` in the plane is represented by the complex number

> {{< latex >}}z = x + iy{{< /latex >}}
> This can be rotated trhough an angle {{< inline-latex "\theta" >}} by multiplying it by {{< inline-latex "e^{i\theta}" >}}, then expanding the product using [[wiki:Euler's formula]]() as follows:

> ...


The important part is that Racket can do the complex multiplication for us. Even better, we only have to deal with two cases: left or right rotation by 90° / {{< inline-latex "\pi/2" >}}. Expanding {{< inline-latex "e^{i\theta}" >}}:

{{< latex >}}e^{i\pi/2} = i{{< /latex >}}
{{< latex >}}e^{-i\pi/2} = -i{{< /latex >}}


What's that? Left rotation is just multiplying by {{< inline-latex "i" >}} and right rotation, multiplication by {{< inline-latex "-i" >}}. Dang. That's easy. Take that, a rule to increment each state by one (modulus the number of states), and a rule to add the direction to the location (for the new location) and we have an update function.

```scheme
; Update an ant
(define (tick a)
  ; Unpack the previous ant, get the current cell
  (match-define (ant rule location direction grid) a)
  (define cell (hash-ref grid location 0))

  ; Rotate, multiply by e^iθ, which for 90° left or right is ±i
  (define new-direction (* direction (if (eq? #\L (string-ref rule cell)) 0+i 0-i)))

  ; Create and return the new ant
  ; Update the position via direction and move to the next state (wrapping)
  (ant rule
       (+ location new-direction)
       new-direction
       (hash-set grid location (remainder (+ cell 1) (string-length rule)))))
```

{{< doc racket "match-define" >}} is a great way to unpack the structure. `cell` holds the current state (since we need that both for the new facing and the new state). The direction is the multiplication as explained above and the new location just adds the old location and direction.

Nice and clean. I love it. Even better, it's completely functional. We're not actually mutating anything, even the call to {{< doc racket "hash-set" >}} creates a new hash rather than modifying the current one.

If we want to see the first few ticks of the `LR` ant:

```scheme
> (define a (make-ant "LR"))
> (tick a)
(ant "LR" -1 -1 '#hash((0 . 1)))
> (tick (tick a))
(ant "LR" -1-1i 0-1i '#hash((0 . 1) (-1 . 1)))
> (tick (tick (tick a)))
(ant "LR" 0-1i 1 '#hash((0 . 1) (-1-1i . 1) (-1 . 1)))
```

Take it from me, that's exactly what we're looking for. But it would be nice if we had a way to visualize it. Eventually, we'll want to generate actual images, but before we do that, let's do some ASCII art.

First, since the grid is allowed to grow unbounded, we first need to figure out how large of a grid we need to draw. Something like this:

```scheme
; Return the current bounds for an ant
(define (bounds a)
  (for/fold ([min-x +inf.0] [max-x -inf.0] [min-y +inf.0] [max-y -inf.0])
            ([(index cell) (in-hash (ant-grid a))])
    (values (min min-x (real-part index))
            (max max-x (real-part index))
            (min min-y (imag-part index))
            (max max-y (imag-part index)))))
```

I like how {{< doc racket "for/fold" >}} can be used to generate multiple values all at once, in this case both the min and max for both x and y.

Okay, with that, we render ASCII:

```scheme
; Render an ant into ASCII characters
(define (render/ascii a [charset " .:-=+*#%@"])
  ; Unpack the ant and determine how large of a grid we need
  (match-define (ant rule location direction grid) a)
  (define-values (min-x max-x min-y max-y) (bounds a))

  ; Sanity check the given charset
  (when (> (string-length rule) (string-length charset))
    (error 'render-ascii "Charset is not longer enough, need ~a, given ~a" (string-length rule) (string-length charset)))

  ; Render an ASCII grid to current-output-port
  ; inexact->exact is necessary to avoid floating point hash errors
  (for ([y (in-range min-y (+ max-y 1))])
    (for ([x (in-range min-x (+ max-x 1))])
      (define p (inexact->exact (make-rectangular x y)))
      (display (string-ref charset (hash-ref grid p 0))))
    (newline)))
```

We have a bit of error handling, which also unfortunately means that we can't deal with more than 10 characters. But it looks pretty good:

```scheme
> (define a (make-ant "LR"))
> (render/ascii (tick a))
.
> (render/ascii (tick (tick a)))
..
> (render/ascii (tick (tick (tick a))))
.
..
```

Hmm. Not very impressive. Let's write a function to do a bunch of ticks in a row.

```scheme
; Run multiple ticks sequentially
(define (fast-tick a n)
  (for/fold ([a a]) ([i (in-range n)])
    (tick a)))

> (render/ascii (fast-tick a 10))
..
..
 ..

> (render/ascii (fast-tick a 1000))
       ..    ..
      .  .    ..
     ...     .. .
  .. . ....     .
 .  ...     ..
.      ......  .
.   . ...  ..  .
.  ...   ..  . .
.   .      ......
.    .. ...   ....
.  .. ..  ...
 .   ....   ...... .
 ...  ...    .   ...
 . .. ....  .  .  .
      ..  .  .  ..
           ..
```

Now, we're getting somewhere. Remember how we already built in some support for more than two character rules? Let's try a few more:

```scheme
> (render/ascii (fast-tick (make-ant "LRL") 100))
   ..
  .  .
 .   :
.   .:
.   . .
 .    .
  .::.

> (render/ascii (fast-tick (make-ant "LRRL") 100))
......
.----.
.::.
:---.
:... .
.::...
```

Okay. A picture may be worth a thousand words, but these need a little work. Better yet would be an animation. To make that easier (using {{< doc racket "big-bang" >}} as I often do), let's use {{< doc racket "2htdp/image" >}} to make some pretty pictures:

```scheme
; Render using htdp
(define (render/htdp a [colors '#("white" "black" "red" "blue" "green" "yellow" "magenta" "cyan" "gray" "pink")])
  ; Unpack the ant and determine how large of a grid we need
  (match-define (ant rule location direction grid) a)
  (define-values (min-x max-x min-y max-y) (bounds a))

  ; Sanity check that we have enough colors, then generate some
  (when (> (string-length rule) (vector-length colors))
    (error 'render-ascii "Not enough colors, need ~a, given ~a" (string-length rule) (vector-length colors)))

  ; Generate the raw images
  (define images
    (for/list ([y (in-range   (- min-y 1) (+ max-y 2))])
      (for/list ([x (in-range (- min-x 1) (+ max-x 2))])
        (define p (inexact->exact (make-rectangular x y)))
        (define c (vector-ref colors (hash-ref grid p 0)))
        (define block (rectangle 10 10 "solid" c))
        (if (= p location)
            (rotate (case direction [(0+i) 0] [(1) 90] [(0-i) 180] [(-1) 270])
                    (overlay (isosceles-triangle 5 45 'outline "red")
                             (isosceles-triangle 5 45 'solid "black")
                             block))
            block))))

  ; Combine them
  (define null (empty-scene 0 0))
  (foldl above null (map (λ (row) (foldl beside null row)) images)))
```

Even better, this time we have the actual ant represented as a red outlined triangle (to show facing). Let's render a few of those previous images:

```scheme
> (render/2htdp (fast-tick (make-ant "LR") 10))
```
{{< figure src="/embeds/2014/LR-10.png" >}}

```scheme
> (render/2htdp (fast-tick (make-ant "LR") 1000))
```
{{< figure src="/embeds/2014/LR-1000.png" >}}

```scheme
> (render/2htdp (fast-tick (make-ant "LRL") 100))
```
{{< figure src="/embeds/2014/LRL-100.png" >}}

```scheme
> (render/2htdp (fast-tick (make-ant "LRRL") 100))
```
{{< figure src="/embeds/2014/LRRL-100.png" >}}

Beautiful. Let's animate it:

```scheme
; Simulate a rule using big bang
(define (simulate rule [width 800] [height 600])
  (define background (empty-scene width height))
  (big-bang (make-ant rule)
    [on-tick tick]
    [to-draw (λ (ant) (overlay (render/2htdp ant) background))]
    [record? #t]))
```

I love how what should theoretically be the most complicated part is actually so simple. Both the basic simulation itself (8 lines without comments) and the simulation loop (6 lines) are tiny. The rendering is a bit worse, but still not that bad. And you can get some *crazy* behavior with these things...

```scheme
> (simulate "LR")
```
{{< figure src="/embeds/2014/LR.gif" >}}

```scheme
> (simulate "LRRL")
```
{{< figure src="/embeds/2014/LRRL.gif" >}}

It's interesting how this one makes such a regular grid.

```scheme
> (simulate "LRRRLRLRL")
```
{{< figure src="/embeds/2014/LRRRLRLRL.gif" >}}

And this one is forming a nice black (state 1) border which keeps getting pushed out further and further.

The basic Langton's Ant (`LR`) is actually fairly famous for it's behavior:


* *simplicity* - < ~300 steps, simple, symmetric patterns
* *chaos* - < ~10,000 steps, large irregular blocks
* *order* - > ~10,000 steps, a recurrent "highway" cycle, 104 blocks in length


Examples:

```scheme
> (render/2htdp (fast-tick (make-ant "LR") 300))
```
{{< figure src="/embeds/2014/LR-300.png" >}}

```scheme
> (render/2htdp (fast-tick (make-ant "LR") 9000))
```
{{< figure src="/embeds/2014/LR-9000.png" >}}

```scheme
> (render/2htdp (fast-tick (make-ant "LR") 11000))
```
{{< figure src="/embeds/2014/LR-11000.png" >}}

```scheme
> (render/2htdp (fast-tick (make-ant "LR") 15000))
```
{{< figure src="/embeds/2014/LR-15000-half.png" >}}

Let it run forever, it just runs off in that one direction. It's actually really interesting:

> Finally the ant starts building a recurrent "highway" pattern of 104 steps that repeat indefinitely. All finite initial configurations tested eventually converge to the same repetitive pattern, suggesting that the "highway" is an attractor of Langton's ant, but no one has been able to prove that this is true for all such initial configurations. It is only known that the ant's trajectory is always unbounded regardless of the initial configuration[4] – this is known as the Cohen-Kung theorem.

> -- [[wiki:Langton's Ant]]()


And that's about it. Surprisingly simple, yet awesome emergent behavior.

Here are a few more fun examples:

```scheme
> (render/2htdp (fast-tick (make-ant "RLLRR") 1000))
```
{{< figure src="/embeds/2014/RLLRR-1000-cyclops.png" >}}

```scheme
> (render/2htdp (fast-tick (make-ant "LRLRLR") 1000))
```
{{< figure src="/embeds/2014/LRLRLR-1000-link.png" >}}

That's actually an interesting aspect: repeated rules form the same patterns, just with different colors. This makes sense if you think about it, since you're getting the same pattern of `L` and `R`, just on a larger space. So:

```scheme
> (render/2htdp (fast-tick (make-ant "LR") 1000))
```
{{< figure src="/embeds/2014/LR-1000.png" >}}

```scheme
> (render/2htdp (fast-tick (make-ant "LRLR") 1000))
```
{{< figure src="/embeds/2014/LRLR-1000.png" >}}

```scheme
> (render/2htdp (fast-tick (make-ant "LRLRLR") 1000))
```
{{< figure src="/embeds/2014/LRLRLR-1000-link.png" >}}

And that's it for today. Take a look; if you find any other awesome patterns, leave a comment! If you want to see the entire source, you can do so (as always) on GitHub: [langtons-ant.rkt](https://github.com/jpverkamp/small-projects/blob/master/blog/langtons-ant.rkt)

[^1]: We'll get to visualizing these shortly

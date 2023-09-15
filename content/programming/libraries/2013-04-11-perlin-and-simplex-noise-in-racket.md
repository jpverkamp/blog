---
title: Perlin and simplex noise in Racket
date: 2013-04-11 14:00:28
programming/languages:
- Racket
- Scheme
programming/topics:
- Games
- Graphics
- Mathematics
- Noise
---
Many games need noise. No, not [[wiki:Noise|that noise]]()--[[wiki:Perlin noise|this noise]](). Or better yet, [[wiki:Simplex noise|this noise]](). More seriously, noise in this context refers to psuedo-randomly generated images that can be used for natural looking terrain generation[^1]. Something like this:

{{< figure src="/embeds/2013/simplex-colored-256x256-16x.png" >}}

<!--more-->

So how do we generate such images? Essentially, you want to write a function that takes coordinates (in 1-, 2-, 3- or even more dimensional space) and returns a single value. Calling the function multiple times for the same coordinate will always return the same value, thus the psudeo-random nature of the algorithm. This also allows for things like persistent level generation using only a seed, such as <a title="Minecraft Wiki: Seed (level generation)" href="http://www.minecraftwiki.net/wiki/World_Generation_Seeds">world generation</a> in <a title="Minecraft" href="https://minecraft.net/">Minecraft</a>.

One simple idea might be to use a simple seeded random number generator. For example, we could do something like the following:

```scheme
(define (seeded x [y 0] [z 0])
  (random-seed (+ x y z))
  (- (* 2.0 (random)) 1.0))
```

And we can test it like so:

```scheme
> (for/list ([i (in-range 5)])
    (for/list ([j (in-range 5)])
      (round-to (seeded i j) 2)))
'((0.71 0.01 0.3 0.89 0.79)
  (0.01 0.3 0.89 0.79 -0.22)
  (0.3 0.89 0.79 -0.22 -0.92)
  (0.89 0.79 -0.22 -0.92 0.83)
  (0.79 -0.22 -0.92 0.83 0.64))
```

So long as they haven't changed the PRNG backing Racket, you should be able to type in that code and get exactly the same values. Every time you run the function, you'll get the same values. We could even turn it into a pretty picture:

```scheme
(build-image
 256 256
 (lambda (x y)
   (define g (clamp -1.0 1.0 (seeded x y)))
   (float-color g g g)))
```

`build-image` is from the Racket package {{< doc racket "picturing-programs" >}}. `clamp` and `float-color` are defined in <a title="noisy-image-test.rkt" href="https://github.com/jpverkamp/noise/blob/master/noisy-image-test.rkt">noisy-image-test.rkt</a> which you can see on GitHub (and I'll talk more about them later).

In any case, using the above code you'll get something (exactly) like this:

{{< figure src="/embeds/2013/seeded-plus.png" >}}

Not exactly what we were hoping for. What's going on here is that because we used `(+ x y z)` as our seed, the function will return the same value for the points (0 1) and (1 0). Not exactly something that we want. But luckily, there are all sorts of more interesting functions that we could use to generate the random seed. For example, we could multiple the numbers together.

{{< figure src="/embeds/2013/seeded-mul-0.png" >}}

Well, no. Actually we can't. It turns out that if we multiple the number but are only generating the x and y, then we're always multiplying by 0. We can fix this pretty easily by changing the line in the `build-image` call from `(seeded x y)` to `(seeded x y 1)`. This gives us a much more reasonable result:

{{< figure src="/embeds/2013/seeded-mul.png" >}}

There are also some options that you can use that will give you some really interesting results. For example, if you use `bitwise-xor` instead of `+` or `*`, you'll get this:

{{< figure src="/embeds/2013/seeded-xor.png" >}}

It's not particularly useful for what we're looking for at the moment, but it's still really cool.

One problem that all of these images have that we want to try and solve is that none of them are particularly 'smooth'. Neighboring values have essentially no relation to each other, so if we tried to use them directly to generate something like terrain, it's going to look obviously artificial. So what we really want is not only a consistent pseudo-random function, but also one that is smooth.

There are a number of ways that we could go about this, but to make a long story shorter[^2] two of the most commonly used algorithms are called [[wiki:Perlin noise]]() and [[wiki:simplex noise]](). Both algorithms were originally implemented by [[wiki:Ken Perlin]](), Perlin noise in the 1980s[^3] and simplex noise in 2001.

Browsing around the Internet, I found a relatively clean and well commented version for both of them in <a title="PDF describing Perlin and simplex noise" href="http://webstaff.itn.liu.se/~stegu/simplexnoise/simplexnoise.pdf">this PDF</a>. The original code was written in C, but it was surprisingly straightforward to convert it to Racket. It's certainly not the fastest code (I haven't really gone that far into optimizing Racket code. If anyone has any advice for as such, I'd love to hear it!), but it does exactly what it's designed to do. Here is the code on GitHub: <a title="noise source on GitHub" href="https://github.com/jpverkamp/noise/blob/master/noise.rkt">noise.rkt</a>.

Really, there are two functions of interest:

```scheme
; Generate 1D/2D/3D Perlin noise
; Always uses a 3D generator in the background
(perlin x [y 0.0] [z 0.0])

; Generate 1D/2D/3D simplex noise
; Always uses a 3D generator in the background
(simplex x [y 0.0] [z 0.0])
```

In each case, you can specify one to three dimensions. For example, these are all valid calls:

```scheme
> (for/list ([i 10]) (round-to (perlin (/ i 10)) 2))
'(0.0 0.11 0.23 0.37 0.46 0.5 0.46 0.37 0.23 0.11)

> (for/list ([i 10]) 
    (for/list ([j 10])
      (round-to (simplex (/ i 10) (/ j 10)) 2)))
'((0.0 0.44 0.68 0.63 0.32 -0.01 -0.1 0.08 0.39 0.67)
  (0.44 0.81 0.94 0.78 0.43 0.12 0.05 0.22 0.46 0.63)
  (0.69 0.94 0.95 0.72 0.38 0.12 0.06 0.16 0.3 0.41)
  (0.67 0.79 0.73 0.51 0.24 0.03 -0.05 -0.05 0.02 0.1)
  (0.5 0.5 0.4 0.25 0.11 -0.02 -0.15 -0.23 -0.23 -0.15)
  (0.31 0.24 0.16 0.12 0.08 0.0 -0.15 -0.29 -0.33 -0.27)
  (0.14 0.09 0.07 0.11 0.15 0.1 -0.04 -0.2 -0.29 -0.27)
  (-0.08 -0.05 0.01 0.12 0.22 0.23 0.13 -0.03 -0.16 -0.24)
  (-0.39 -0.26 -0.11 0.07 0.23 0.3 0.26 0.13 -0.07 -0.28)
  (-0.67 -0.45 -0.22 -0.01 0.16 0.26 0.27 0.15 -0.09 -0.39))

> (perlin 3.14 1.59 2.65)
-0.3772216257243449
```

Both of the functions will scale roughly in the range [-1.0, 1.0] as in the original implementation. If you look closely and sort of squint, these functions have something that the original functions didn't have: they're smooth. Values generated on coordinates near to each other are similar. It will be much easier if we happened to have functions that could visualize these. {{< doc racket "picturing-programs" >}} to the rescue!

Using essentially the same code as before, we now have everything we need to generate these images. As I said, there are two helper functions that I needed to write. `clamp` will take a number in the range [-1.0, 1.0] (or any range really) and scale it to [0.0, 1.0]. `float-color` takes [[wiki:RGB]]()values in the range [0.0, 1.0] and scales them to bytes in the range [0, 255] so we can make a color. You can see the code for both of those <a title="noisy-image-test.rkt" href="https://github.com/jpverkamp/noise/blob/master/noisy-image-test.rkt">on GitHub</a>--they should be pretty straight forward.

With that, here's a function that can generate any sized image (with a scaling factor) from Perlin noise:

```scheme
; Build an image using perlin noise
(define (build-perlin-image w h #:scale [scale 1.0])
  (build-image 
   w h
   (lambda (x y)
     (define g (clamp -1.0 1.0 (perlin (* scale (/ x w))
                                       (* scale (/ y h)))))
     (float-color g g g))))
```

Here are a bunch of images I've generated using the Perlin/simplex image functions:


|                 |                 1x                  |                   4x                   |                 |                                     |                                        |
|-----------------|-------------------------------------|----------------------------------------|-----------------|-------------------------------------|----------------------------------------|
|     perlin      |     {{< figure src="/embeds/2013/perlin-256x256.png" >}}      |     {{< figure src="/embeds/2013/perlin-256x256-4x.png" >}}      |                 |                                     |                                        |
|     simplex     |     {{< figure src="/embeds/2013/simplex-256x256.png" >}}     |     {{< figure src="/embeds/2013/simplex-256x256-4x.png" >}}     | colored simplex | {{< figure src="/embeds/2013/simplex-colored-256x256.png" >}} | {{< figure src="/embeds/2013/simplex-colored-256x256-4x.png" >}} |
| colored simplex | {{< figure src="/embeds/2013/simplex-colored-256x256.png" >}} | {{< figure src="/embeds/2013/simplex-colored-256x256-4x.png" >}} |                 |                                     |                                        |


If you'd like to check out the entire project, you can do so here:
<a href="https://github.com/jpverkamp/noise" title="noise on GitHub">noise</a>

If you have any comments about either coding style or optimizations, I'd love to hear them. It's certainly not pure functional code but rather a more or less direct translation of the original Java (I did clean up a few things).

[^1]: Among many, many other uses
[^2]: Too late...
[^3]: He actually won a [[wiki:Academy Award for Technical Achievement]]() for it in 1997. I didn't even know that was a thing...
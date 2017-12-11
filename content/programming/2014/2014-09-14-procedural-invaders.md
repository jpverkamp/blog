---
title: Procedural Invaders
date: 2014-09-14 09:00:00
programming/languages:
- Racket
- Scheme
programming/topics:
- Games
- Graphics
- Procedural Content
---
Today's post comes from a long line of 'inspired by posts' all pretty much leading back (so far as I can tell) to this post by j.tarbell: <a href="http://www.complexification.net/gallery/machines/invaderfractal/">invader.procedural</a> from 2003.

The basic idea is that we want to generate 'invaders' in the style of {{< wikipedia "space invaders" >}}. Except we don't want 10 or 20, we want tens of thousands. So how do we do it? Well, take a look at this:

{{< figure src="/embeds/2014/procedural-invader-big.png" >}}

<!--more-->

Despite the fact that it's scaled up, on the lowest level we actually have a 5x5 grid of pixels. In addition, it's mirrored to make it symmetrical, so (counting the non-mirrored center row), we actually only have 15 pixels:

```text
+----+----+----+----+----+
|  1 |  6 | 11 |  6 |  1 |
+----+----+----+----+----+
|  2 |  7 | 12 |  7 |  2 |
+----+----+----+----+----+
|  3 |  8 | 13 |  8 |  3 |
+----+----+----+----+----+
|  4 |  9 | 14 |  9 |  4 |
+----+----+----+----+----+
|  5 | 10 | 15 | 10 |  5 |
+----+----+----+----+----+
```

Represent those 15 pixels as a 15 bit number. For example, the above image, we have bits 2, 4, 6, 7, 8, 10, 13, and 15 set, so we have the number:

```scheme
> #b010101110100101
11173
```

Given that there are over 32 thousand 15 bit numbers ({{< inline-latex "2^{15" >}}=@(expt 2 15)}), that's a lot of invaders. So how do we generate them?

```scheme
; Create a symmetric 5x5 image similar to a space invader with this bit pattern
; 0 5 10 5 0
; 1 6 11 6 1
; 2 7 12 7 2
; 3 8 13 8 3
; 4 9 14 9 4
(define (procedural-invader i)
  (define bits
    (for/vector ([c (in-string (~a (number->string i 2) #:width 15 #:pad-string "0" #:align 'right))])
      (eq? c #\1)))

  (build-flomap*
   1 5 5
   (λ (x y)
     (define i (+ y (* 5 (if (< x 3) x (- 4 x)))))
     (if (vector-ref bits i) '#(1.0) '#(0.0)))))
```

There are really two parts here. First we covert the given integer into a vector of `#t` / `#f`. There are certainly far faster ways to do this (`bitwise-and` with the correct bit for example), but given that the size is set and small, this is good enough for the time being.

After that, we take those bits and use {{< doc racket "build-flomap*" >}} to create a 5x5 image where `#t` is white and `#f` is black. Shiny. Now unfortunately Dr. Racket will not display flomaps directly inline, but if we convert them to bitmaps it will:

```scheme
> (flomap->bitmap (procedural-invader 11173))
```

{{< figure src="/embeds/2014/procedural-invader-tiny.png" >}}

Oof. Tiny. Let's make it bigger:

```scheme
> (flomap->bitmap (flomap-resize (procedural-invader 11173) 50 50))
```

{{< figure src="/embeds/2014/procedural-invader-big-blurry.png" >}}

Well that's not what I was looking for. The problem is that flomaps by default are designed for interpolated values. So that if you have a black pixel right next to a white pixel, you can actually ask for the 'pixel' halfway between the two, getting a gray value. But in this case, that's not what we want. We want sharp ({{< wikipedia "nearest neighbor" >}}) scaling:

```scheme
; Resize a flomap using nearest-neighbors to preserve sharp edges
(define (flomap-resize/nn img new-width [new-height new-width])
  (match-define (flomap _ components old-width old-height) img)

  (build-flomap*
   components new-width new-height
   (λ (new-x new-y)
     (flomap-ref* img
                  (floor (* old-width (/ new-x new-width)))
                  (floor (* old-height (/ new-y new-height)))))))
```

Same as before, we are creating a new image. But this time, we covert the old coordinate system to the new and throw away any of the decimal part, getting an exact answer. That way we never interpolate:

```scheme
> (flomap->bitmap (flomap-resize/nn (procedural-invader 11173) 50 50))
```

{{< figure src="/embeds/2014/procedural-invader-big.png" >}}

Nice and sharp. That's exactly what we were looking for.

For the base of the problem, that's pretty much it. But we're not quite done. What if we want to make a nice display mode so that we can see a bunch of them at once?

```scheme
; Generate a demo shee\t of procedural invaders
(define (demo [rows 5] [cols rows] #:image-size [image-size 20] #:margins [margins 5])
  (define images
    (for/list ([row (in-range rows)])
      (for/list ([col (in-range cols)])
        (define r (random 32768))
        (define img (procedural-invader r))
        (flomap->bitmap (flomap-add-margin (flomap-resize/nn img image-size) margins)))))

  (cond
    [(and (= rows 1) (= cols 1))
     (caar images)]
    [(= rows 1)
     (car (map (curry apply beside) images))]
    [(= cols 1)
     (apply above (map car images))]
    [else
     (apply above (map (curry apply beside) images))]))
```

That way we can make nice mixed sheets of the things:

```scheme
> (demo)
```

{{< figure src="/embeds/2014/procedural-invaders.png" >}}

Or even giant sheets:

```scheme
> (demo 40 80 #:image-size 5 #:margins 1)
```

{{< figure src="/embeds/2014/procedural-invaders-80x40.png" >}}

Pop quiz: Find two identical invaders. What is the likelihood of that happening? Well using the same math as in [The Birthday Paradox]({{< ref "2012-10-01-the-birthday-paradox.md" >}}), the chance of no duplicates is:

{{< latex >}}B(n, x) = 1 - \prod_{i=1}^{(n-1)}(1-\frac{i}{x}){{< /latex >}}

Where {{< inline-latex "n" >}} is the number of generated invaders and {{< inline-latex "x = 15^{2" >}} = 32768} is the total number of possible invaders.

Specifically, for the 5x5 case:

{{< latex >}}B(25, 32768)
  = 1 - \prod_{i=1}^{(25-1)}(1-\frac{i}{32768})
  \approx 9.1\%{{< /latex >}}

And for the 80x40 case:

{{< latex >}}B(3200, 32768)
  = 1 - \prod_{i=1}^{(3200-1)}(1-\frac{i}{32768})
  \approx 100\%{{< /latex >}}

So it's (almost certainly) there... you just have to find it. :smile:

Okay, what else can we do with these things? Well, at the moment, they're a little bit bland. Let's add a few bits to the generation and spice them up a bit with highlights. Specifically, let's choose one of the 15 bits to be red instead of black or white. In order to do that (choose 1 of 15), we need 4 bits (with one left over). SOmething like this should work:

```scheme
; Create a procedural invader as above, but highlight the point specified by four highest bits
(define (procedural-invader/highlight i)
  (define highlight (bitwise-and i #b1111))
  (define img-w/o-highlight (procedural-invader (arithmetic-shift i -4)))

  (build-flomap*
   3 5 5
   (λ (x y)
     (define i (+ y (* 5 (if (< x 3) x (- 4 x)))))
     (if (= highlight i)
         '#(1.0 0.0 0.0)
         (make-vector 3 (flomap-ref img-w/o-highlight 0 x y))))))
```

Basically, we pull off the lowest four bits with a {{< wikipedia "bitmask" >}} for the highlight then shift all the rest down and pass off to the original `procedural-invader` function. Then we build a new image from that, mostly copying but taking a single pixel and making it red. Adding an argument so that our `demo` function can handle highlighting:

```scheme
> (demo #:highlights? #t)
```

{{< figure src="/embeds/2014/procedural-invaders-highlights.png" >}}

Or even giant sheets:

```scheme
> (demo 40 80 #:image-size 5 #:margins 1 #:highlights? #t)
```

{{< figure src="/embeds/2014/procedural-invaders-80x40-highlights.png" >}}

Ooh. That's starting to look like a game. Perhaps I'll revist these for the next [Ludum Dare]({{< ref "2013-05-21-ludum-dare-26-vtanks-results.md" >}})...

What else can we do with these? Well, take the <a href="http://www.complexification.net/gallery/machines/invaderfractal/">post I was inspired by</a>. In that case, they fill up a space with procedural invaders of different sizes. That would be neat to check out. I've started implementing something...

{{< figure src="/embeds/2014/fractal-invaders.png" >}}

But it's not quite right yet. Perhaps next time...

If you'd like to check out the entire code for today's post, as always, it's available on GitHub: <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/procedural-invaders.rkt">procedural-invaders.rkt</a>

---
title: Fractal Invaders
date: 2014-09-16 09:00:00
programming/languages:
- Racket
- Scheme
programming/topics:
- Fractals
- Games
- Graphics
- Procedural Content
---
Today's post is a follow up to Sunday's post [Procedural Invaders]({{< ref "2014-09-14-procedural-invaders.md" >}}). This time around, we're going to work through two different space filling algorithms in order to eventually generate something like this:

{{< figure src="/embeds/2014/fractal-invaders-100x100.png" >}}

<!--more-->

But before we get to that image, let's start with where I was Sunday. We had something that looked like this:

{{< figure src="/embeds/2014/random-invaders.png" >}}

That was my first take at a fractal invader algorithm, and in that case there really wasn't anything to do with fractals at all. The basic algorithm for that was simple:


* Choose a random location and size for an invader
* If the new invader does not collide with any previous invader, place it
* Go to step 1


If we failed 100 times in a row to place an invader, we made the assumption that the space was empty and bailed out. It actually worked well enough. You got to see a bunch of invaders of different sizes, all together on the map. Unfortunately though, it didn't work particularly well for filling the entire space, which is really what I was after. (If you'd like you can see the code for that on GitHub in Sunday's code: <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/procedural-invaders.rkt">procedural-invaders.rkt</a>).

After that though, I took a step back. How can we actually fill the space? More specifically, how can we use recursion / fractals to efficiently fill the space? Well, what we really need is actually really similar to another previous post of mine: [Quadtree image compression]({{< ref "2014-05-28-quadtree-image-compression.md" >}}).

Basically, here's the new algorithm:


* Given a rectangular region, choose a random location and size for an invader
* Recursively divide the remaining space into four sections: one above, one to the right, one below, and one to the left of the new invader
* If any region is small enough for only a single invader, place it and stop (base case)
* For each other region, start again at step 1


The main odd step there is step 2 above. How can we split a region into five subregions (the center being square) like that? Well, we could do something like this:

```text
| R
      | i
 Top  | g
______| h
   |  | t
 L |__|____
 e |
 f | Bottom
 t |
```

Making sure that you have all of the regions set up exactly right gets a little bit complicated, but if you draw a nice diagram, it should be fairly straight forward to make sure that you always generate this structure. And that's exactly what we have here:

```scheme
(struct rect (t l w h) #:transparent)
(struct node (bounds value-bounds value children) #:transparent)

; Create the recursive fractal structure
(define (made-fractal width height random-node)
  (let loop ([t 0] [l 0] [w width] [h height])
    (cond
      ; The next node is too small, do not place it
      [(or (<= w 0) (<= h 0) (>= t height) (>= l width))
       #f]
      ; Create a child node; recur four times as so:
      ;  T  |
      ; __  |
      ;   XX R
      ; L XX__
      ;   |
      ;   | B
      [else
       (define s (if (= (min w h) 1) 1 (+ 1 (random (min w h)))))
       (define x (if (= w s)         0 (random (- w s))))
       (define y (if (= h s)         0 (random (- h s))))
       (node (rect t       l       w h) ; Bounds of this node
             (rect (+ t y) (+ l x) s s) ; Bounds of the value within this node
             (random-node)              ; The value of this node
             (list (loop t         l         (+ x s)   y        )
                   (loop t         (+ l x s) (- w x s) (+ y s)  )
                   (loop (+ t y s) (+ l x)   (- w x)   (- h y s))
                   (loop (+ t y)   l         x         (- h y)  )))])))
```

Essentially, we want to create a nested structure made out of `node` structs. For each node, we have two bounding boxes, one for the entire recursive structure and one just for the central image (which in turn defines the four children). Then we have a value which I've already parameterized here as the `random-node` parameter and finally four children (ordered top, right, bottom, left, although it really doesn't matter).

What's neat about this is that the exact same code could theoretically be used for other structures. Say if we wanted 8 children for each of the orthagonal or diagonal directions. Just add more to the `node-children` list.

There are a few edge cases to watch out for that I did spend rather a while working out. For example, the base case deals with cases where either `w` or `h` is less than zero, but it also deals when we go off the right or bottom edge of the region. Likewise, we have to check if we only have exactly 1 square left in either width or height (which would mean we cannot generate an interesting random size) or if we only have exactly enough room for one shape.

After that, it's just a matter of getting the parameters right for the recursive calls. Let's try one out:

```scheme
> (make-fractal 4 3 (const #t))
(node
 (rect 0 0 4 3)
 (rect 0 0 3 3)
 #t
 (list
  #f
  (node
   (rect 0 3 1 3)
   (rect 1 3 1 1)
   #t
   (list
    (node (rect 0 3 1 1) (rect 0 3 1 1) #t '(#f #f #f #f))
    #f
    (node (rect 2 3 1 1) (rect 2 3 1 1) #t '(#f #f #f #f))
    #f))
  #f
  #f))
```

If you take each of those in order, you have the regions:

```text
AAAB
AAAC
AAAD
```

So we generated a 3x3 region first and then filled in the rest with 1x1s. Of course that's not very nice to visualize. Let's make something a little prettier:

```scheme
(define (in? bounds x y)
  (match-define (rect t l w h) bounds)
  (and (<= l x (+ l w -1))
       (<= t y (+ t h -1))))

; Render a fractal image
(define (fractal-image
         width height
         #:random-color [random-color (thunk (vector (random) (random) (random)))])

  (define root (make-fractal width height random-color))

  (flomap->bitmap
   (build-flomap*
    3 width height
    (λ (x y)
      (let loop ([node root])
        (cond
          [(in? (node-value-bounds node) x y) (node-value node)]
          [else
           (for*/first ([child (in-list (node-children node))]
                        #:when (and child (in? (node-bounds child) x y)))
             (loop child))]))))))
```

That's surprisingly simple, but then again most of the work was already done in setting up the structure. The most complicated bit here is that we have two different usages of the `in?` function:


* `(in? (node-value-bounds node) x y)` - checks if the current point is in the current node's value box (the inner box); if that's the case, this is our base case
* `(in? (node-bounds child) x y)` - if this is true for any of the child node's outer box; if that's true we know that our value is somewhere in that subtree


That's all we need to make some pretty neat images, just changing how we generate colors:

```scheme
> (fractal-image 200 200)
```

{{< figure src="/embeds/2014/fractal-image-random.png" >}}

```scheme
> (fractal-image 200 200 #:random-color (thunk (let ([g (random)]) (vector g g g))))
```

{{< figure src="/embeds/2014/fractal-image-gray.png" >}}

```scheme
> (fractal-image 200 200
                 #:random-color (thunk
                                  (case (random 3)
                                    [(0) (vector (random) 0 0)]
                                    [(1) (vector 0 (random) 0)]
                                    [(2) (vector 0 0 (random))])))
```

{{< figure src="/embeds/2014/fractal-image-rgb.png" >}}

Which, honestly, would be a pretty neat post all by itself. But wasn't the entire point of this to made a fractal out of the [procedural invaders]({{< ref "2014-09-14-procedural-invaders.md" >}})?

```scheme
; Render a fractal image made of invaders!
(define (fractal-invaders width height #:highlights? [highlights? #f])
  (define (random-invader)
    (flomap-add-margin
     (if highlights?
         (procedural-invader/highlight (random 524288))
         (procedural-invader (random 32768)))
     1))

  (define root (make-fractal (quotient width 7)
                             (quotient height 7)
                             random-invader))

  (flomap->bitmap
   (build-flomap*
    (if highlights? 3 1) width height
    (λ (x y)
      ; Correct for coordinates within the node
      (define nx (quotient x 7))
      (define ny (quotient y 7))

      (let loop ([n root])
        (cond
          [(in? (node-value-bounds n) nx ny)
           ; Calculate coordinates within the image
           (match-define (node _ (rect t l s _) img _) n)
           (define ix (quotient (- x (* 7 l)) s))
           (define iy (quotient (- y (* 7 t)) s))
           (flomap-ref* img ix iy)]
          [else
           (or
            (for*/first ([child (in-list (node-children n))]
                         #:when (and child (in? (node-bounds child) nx ny)))
              (loop child))
            (if highlights? '#(1 1 1) '#(1)))]))))))
```

Okay, this code isn't quite as nice. Mostly, that's because of a simplifying requirement that I started with: we're going to be working with a grid where each 'pixel' is a single minimal size invader. With a 1 pixel margin, that means that our minimum image size is 7x7 (thus the 7s scattered throughout the code).

Unfortunately, that does make our base case a little more complicated, since we're working with two different coordinate systems: image coordinates `x` and `y` and fractal coordinates `nx` and `ny`. Still, add in some offsets by 7 and a bit of padding down at the end (for images not divisible by 7) and off we go:

```scheme
> (fractal-invaders 100 100)
```

{{< figure src="/embeds/2014/fractal-invaders-100x100.png" >}}

It also works great for larger images:

```scheme
> (fractal-invaders 400 200)
```

{{< figure src="/embeds/2014/fractal-invaders-400x200.png" >}}

It even supports highlights:

```scheme
> (fractal-invaders 400 200 #:highlights? #t)
```

{{< figure src="/embeds/2014/fractal-invaders-400x200-highlights.png" >}}

Now that's what I'm talking about. Unfortunately, the process is still somewhat random:

```scheme
> (fractal-invaders 100 100)
```

{{< figure src="/embeds/2014/fractal-invaders-100x100-big.png" >}}

Sometimes the first random image is a little on the annoyingly large size. Off the top of my head, there are two ways to deal with it: either add an option parameter that controls the maximum size of a block or just keep generating images until you get what you are looking for.

Guess which solution I prefer? :smile:

```scheme
(define (fractal-invaders ... #:maximum-invader-size [max-size #f])
  ...
  (define root
    (make-fractal
     (quotient width 7)
     (quotient height 7)
     random-invader
     #:maximum-block-size (and max-size (/ max-size 7))))
  ...)

(define (make-fractal width height random-node #:maximum-block-size [max-size #f])
  ...
      [else
       (define s
         (let loop ()
           (define s (if (= (min w h) 1) 1 (+ 1 (random (min w h)))))
           (cond
             [(or (not max-size) (< s max-size)) s]
             [else (loop)])))
       ...])
```

Simple!

```scheme
> (fractal-invaders 400 200 #:highlights? #t #:maximum-invader-size 25)
```

{{< figure src="/embeds/2014/fractal-invaders-400x200-max-25.png" >}}

Beautiful!

I wonder what other sort of images I could make with a fractal space filling algorithm like this? :innocent:

As always, today's code is available on GitHub. Check it out: <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/fractal-invaders.rkt">fractal-invaders.rkt</a> (Requires <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/procedural-invaders.rkt">procedural-invaders.rkt</a> to run.)

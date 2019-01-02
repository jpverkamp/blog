---
title: "AoC 2018 Day 13: Mine Cart Madness"
date: 2018-12-13
programming/languages:
- Racket
programming/sources:
- Advent of Code
series:
- Advent of Code 2018
---
### Source: [Mine Cart Madness](https://adventofcode.com/2018/day/13)

> **Part 1:** Load a minecart track that looks like this:

> ```
/->-\        
|   |  /----\
| /-+--+-\  |
| | |  | v  |
\-+-/  \-+--/
  \------/
```

> Assuming minecarts follow the tracks and alternate turning left, going straight, and turning right on each intersection (`+`), where does the first collision occur?

> NOTE: Update carts top to bottom, left to right. Carts can collide mid update.

<!--more-->

Okay. It's an interesting data format problem mostly. And we have to deal a bit with not being imperative, in particular when we're doing the updates, since having collisions happen halfway through an update is not so great. Let's load it:

```racket
(struct point (x y) #:transparent)
(struct cart (location velocity next-turn) #:transparent)
(struct track (data carts top-left bottom-right) #:transparent)
```

The goal will be to load the tracks into a hash of `point` to character (so I know how the track turns / intersects) and separately store the carts. I'll want to process the track after the initial load to replace carts with their underlying track and get the initial velocity as well. Finally, `next-turn` will always start as `'left`, but we'll deal with that later.

```racket
; Read a track from the current-input
(define (read-track [in (current-input-port)])
  ; Read the raw data
  (define raw-data
    (for/fold ([track (hash)])
              ([line (in-lines in)]
               [y (in-naturals)])
      (for/fold ([track track])
                ([c (in-string line)]
                 [x (in-naturals)]
                 #:unless (equal? c #\space))
        (hash-set track (point x y) c))))

  ; For each cart character, track to underlying track and current velocity
  (define cart-track-data
    (hash #\> (list #\-  1 0)
          #\< (list #\- -1 0)
          #\^ (list #\| 0 -1)
          #\v (list #\| 0  1)))

  ; Determine where the carts are
  (define-values (data carts)
    (for*/fold ([data raw-data]
                [carts (list)])
               ([(p c) (in-hash raw-data)]
                [ctd (in-value (hash-ref cart-track-data c #f))]
                #:when ctd)
      (values
       ; Overwrite the track point with the underlying track
       (hash-set data p (first ctd))
       ; Store the cart position and velocity
       (list* (cart p (point (second ctd) (third ctd)) 'left) carts))))

  ; Determine the bounds for the track
  (define-values (min-x max-x min-y max-y)
    (for/fold ([min-x #f] [max-x #f] [min-y #f] [max-y #f])
              ([(p c) (in-hash data)])
      (values (min (or min-x (point-x p)) (point-x p))
              (max (or max-x (point-x p)) (point-x p))
              (min (or min-y (point-y p)) (point-y p))
              (max (or max-y (point-y p)) (point-y p)))))

  ; Finally create the track structure
  (track data
         carts
         (point min-x min-y)
         (point max-x max-y)))
```

It's a bit complicated and it turns out that the only reason that I need the bounds is to display the tracks for debug reasons, which amuses me somewhat. But we have it, so let's use it. Speaking of display, here's a function to take those bounds and write out what the current track looks like:

```racket
; Helper function to display a track
(define (display-track m)
  (for ([y (in-range (point-y (track-top-left m)) (add1 (point-y (track-bottom-right m))))])
    (for ([x (in-range (point-x (track-top-left m)) (add1 (point-x (track-bottom-right m))))])
      (cond
        [(for/first ([c (in-list (track-carts m))]
                     #:when (equal? (cart-location c) (point x y)))
           c)
         => (λ (c)
              (display
               (match (cart-velocity c)
                 [(point 0  1) #\v]
                 [(point 0 -1) #\^]
                 [(point  1 0) #\>]
                 [(point -1 0) #\<])))]
        [else
         (display (hash-ref (track-data m) (point x y) #\.))]))
    (newline)))
```

Helpful for debugging. {{< doc racket match >}} is lovely.

Okay, next we want a function to update a single `cart`. We'll use this next to update each cart in turn. This got tricky. Initially, I was checking the carts against the `track` data (to check for collisions), but that doesn't work, since we can have a cart collide against another one after both have already moved. The only way I've seen to track that is to specify the current cart locations to the `update-cart` function. There really should be a more elegant way to do this:

```racket
; Update a cart by one tick
; Return the new cart; but if it collided raise the cart as an exception insteadcurrent-frame
; c* Is a running updated list of carts, since collisions can happen with already moved carts
(define (update-cart m c c*)
  (match-define (cart (point x y) (point vx vy) rotation) c)

  (define new-location (point (+ x vx) (+ y vy)))

  (define-values (new-velocity new-rotation)
    (case (hash-ref (track-data m) new-location)
      [(#\/) (values (point (- vy) (- vx)) rotation)]
      [(#\\) (values (point vy vx) rotation)]
      [(#\+)
       (case rotation
         [(left)     (values (point vy (- vx)) 'straight)]
         [(straight) (values (point vx vy)     'right)]
         [(right)    (values (point (- vy) vx) 'left)])]
      [else  (values (point vx vy) rotation)]))

  (define updated-cart (cart new-location new-velocity new-rotation))

  ; Check for collisions
  (for ([c (in-list c*)]
        #:when (equal? new-location (cart-location c)))
    (raise updated-cart))

  updated-cart)
```

One thing that I actually enjoy here is that I'm using {{< doc racket exception >}} handling to deal with the collisions. The function itself only deals with returning the updated cart. If there's a collision, we'll {{< doc racket raise >}} the cart that caused the problem in order to catch it via {{< doc racket "with-handlers" >}} later.

I'm also pretty proud of the rotation code. There are a few other ways you can do this, for example with matrix multiplication or hard coding each case. But I worked it out on paper and it turns out that you flip x and y and negate one or the other. (It's a symptom of the aforementioned matrix multiplication.)

In any case, we can now update the entire track:

```racket
; Update a track by one tick
; If two carts collide, an exception will be raised, catch it and return the cart
(define (update-track m)
  ; Update carts, has to be done oddly since they can collide half way through an update
  ; Otherwise, remove the third argument from update-cart and use:
  ;   (map (curry update-cart m) (sort (track-carts m) cart-location-<?))
  (define updated-carts
    (let loop ([done '()]
               [todo (sort (track-carts m) cart-location-<?)])
      (cond
        [(null? todo) done]
        [else
         ; TODO: Make this more efficient than using append
         (loop (list* (update-cart m (first todo) (append done todo)) done)
               (rest todo))])))

  (track (track-data m)
         updated-carts
         (track-top-left m)
         (track-bottom-right m)))
```

As the comment notes, I wish we could have done all the carts at a time. But that would lead to carts skipping past each other in cases like this: `->--<-`. So it goes.

Now we can take it one step more and run the simulation until we get a collision. Because we're using exceptions and we haven't caught them yet:

```racket
; Run a track until collision, return the cart that collided
(define (update-track-until-collision m)
  (with-handlers ([cart? identity])
    (let loop ([m m])
      (loop (update-track m)))))

; Run the main program
(printf "[part1]\n")
(define input (read-track))
(update-track-until-collision input)
```

That's fun.

```bash
$ cat input.txt | racket mine-cart-madness.rkt

[part1]
(cart (point 118 66) (point 1 0) 'straight)
```

Whee!

> **Part 2:** Instead of ending the simulation, removing carts that crash into one another. What is the location of the final remaining cart?

This time around, the `updated-carts` function will be caught immediately in this function, triggering the removal of the cart that was removed (with the `(rest todo`) and all other carts at the same location (`remove-by-location`). Voila:

```racket

; Update a track by one tick
; If two carts collide, remove those two carts and contiue updating
(define (update-track/remove-collisions m)
  ; Helper to remove carts at a given location from a list
  (define (remove-by-location carts location)
    (for/list ([c (in-list carts)]
               #:unless (equal? (cart-location c) location))
      c))

  ; Calculate the new list of carts, some might collide
  (define updated-carts
    (let loop ([done '()]
               [todo (sort (track-carts m) cart-location-<?)])
      (cond
        [(null? todo) done]
        [else
         (with-handlers
             ; Case where carts collided
             ; Remove that cart + all other carts with that coordinate from both lists
             ([cart? (λ (c)
                       (loop (remove-by-location done (cart-location c))
                             (remove-by-location (rest todo) (cart-location c))))])
           ; Otherwise
           (loop (list* (update-cart m (first todo) (append done todo)) done)
                 (rest todo)))])))

  (track (track-data m)
         updated-carts
         (track-top-left m)
         (track-bottom-right m)))
```

The wrapper function to run until there is only one cart is only slightly longer:

```racket
; Run a track until there is only one cart left, removing carts that collide
(define (update-track-until-singleton m)
  (let loop ([m m])
    (cond
      [(<= (length (track-carts m)) 1)
       (first (track-carts m))]
      [else
       (loop (update-track/remove-collisions m))])))

; Run the main program again
(printf "\n[part2]\n")
(current-frame 0)
(update-track-until-singleton input)
```

Shiny:

```racket
$ cat input.txt | racket mine-cart-madness.rkt

[part1]
(cart (point 118 66) (point 1 0) 'straight)

[part2]
(cart (point 70 129) (point 0 1) 'right)
```

As a bonus, I made a function that can render the simulation to a picture!

```racket
; Helper function to render a map as a frame to an image with ASCII graphics
(define (render-frame m prefix)
  (match-define (track data carts (point left top) (point right bottom)) m)
  (printf "rendering frame ~a:~a\n" prefix (current-frame))
  (send
   (flomap->bitmap
    (build-flomap*
     3 (add1 (- right left)) (add1 (- bottom top))
     (λ (x y)
       (cond
         ; Carts are red
         [(for/first ([c (in-list carts)]
                      #:when (equal? (point x y) (cart-location c)))
            c)
          (vector 1 0 0)]
         ; Tracks are white
         [(hash-ref data (point x y) #f)
          (vector 1 1 1)]
         ; Background is black
         [else
          (vector 0 0 0)]))))
   save-file
   (~a "frame-" prefix "-" (~a (current-frame) #:min-width 4 #:left-pad-string "0" #:align 'right) ".png")
   'png)
  (current-frame (add1 (current-frame))))
```

Pretty pictures!

```bash
$ cat input.txt | racket mine-cart-madness.rkt --debug-frames
...

$ convert frame-collision-*.png -interpolate Nearest -filter point -resize 200% aoc-13-minecart.gif
```

{{< figure src="/embeds/2018/aoc-13-minecart.gif" >}}

Not super helpful at this scale, but pretty.

---
title: Twitter puddle
date: 2013-11-30 04:55:28
programming/languages:
- Racket
- Scheme
programming/topics:
- Cellular Automata
- Graphics
- Procedural Content
- Twitter
---
This one has been sitting in my backlog for a while and its been a while since I've gotten to write a programming post[^1], but now seems as good time as ever: <a href="http://programmingpraxis.com/2013/11/15/twitter-puddle/">Twitter puzzle</a>

<!--more-->

The basic idea is that you're going to get a series of wall heights representing a bumpy landscape. For example:

```scheme
> (draw-puddle (make-puddle '(2 5 1 2 3 4 7 7 6)))
```

{{< figure src="/embeds/2013/initial-state.png" >}}

(Just ignore the water at the top, this is actually the first state of the simulation that we'll be writing.)

Once we have a world, the goal is to figure out how much water we could store in that world. In this case, any water on either side of the middle pool will fall off the sides, as will water over the left wall in the center. So the final state we're looking for should look something like this:

{{< figure src="/embeds/2013/final-state.png" >}}

So how do we get there?

Well, first we need some way to represent the world. I'm going to go with a two dimensional vector of vectors. Each element will be one of the symbols `empty`, `wall`, or `water`. Something like this:

```scheme
; Twitter puddle structure; 2d grid of item types (empty, wall, water)
(struct puddle (data) #:transparent #:mutable)
```

In addition to that, we probably want a few convince functions. In this case, we'll write a function to turn a list of wall heights into a puddle (as seen above), accessors for the height, and a getter/setter. I'm going to do something a bit interesting with the getter/setter. Rather than forcing the programmer to deal with boundary conditions, I'll just check the bounds here and return `#f` if we can't get/set a value.

```scheme
; Create a puddle from a list of wall heights
(define (make-puddle wall-heights)
  (define w (length wall-heights))
  (define h (add1 (apply max wall-heights)))

  (puddle
   (for/vector ([r (in-range h)])
     (for/vector ([c (in-range w)]
                  [h (in-list wall-heights)])
       (if (< r h) 'wall 'empty)))))

; Getter/setter for puddle data
(define (puddle-ref p r c)
  (with-handlers ([exn? (λ (e) #f)])
    (vector-ref (vector-ref (puddle-data p) r) c)))

(define (puddle-set!? p r c v)
  (with-handlers ([exn? (λ (e) #f)])
    (vector-set! (vector-ref (puddle-data p) r) c v))
  #t)

; Get the size of a puddle
(define (puddle-height p)
  (vector-length (puddle-data p)))

(define (puddle-width p)
  (vector-length (vector-ref (puddle-data p) 0)))
```

From here, we have two options for our simulation. Either we want to step the entire simulation (so that water falls down) or we want to add some new water. For both cases, we'll create a new puddle and mutate that one. That way later when we want to compare the current state to previous states, we can do so. So first, stepping:

```scheme
; Perform one step in puddle simulation
; Try moving each water these directions in order:
; - down, down left, down right, left, right, no move (will always succeed)
(define (step p)
  ; Create the new puddle (if you do it in place, water teleports)
  (define new-p
    (puddle (for/vector ([row (in-vector (puddle-data p))])
              (for/vector ([col (in-vector row)])
                (case col
                  [(empty water) 'empty]
                  [(wall)        'wall])))))

  ; Update each element in turn
  (for ([r (in-naturals)]
        [row (in-vector (puddle-data p))])
    (for ([c (in-naturals)]
          [col (in-vector row)])
      (let/ec break
        (when (eq? 'water col)
          (for ([rd (in-list '(-1 -1 -1  0  0  0  1))]
                [cd (in-list '( 0 -1  1 -1  1  0  0))])
            (case (puddle-ref new-p (+ r rd) (+ c cd))
              [(empty #f)
               (when (puddle-set!? new-p (+ r rd) (+ c cd) 'water)
                 (break))]))))))

  new-p)
```

Essentially, copy the puddle and then check down, diagonally, and finally to the sides. This will help water fill in puddles and drain off to the sides when walls aren't high enough. I'm using a trick I've used before with `let/ec` to basically add early returns to Racket. It's nice how things like that are possible.

Next, dripping. Essentially, we want to create new water along the top. Originally, I had this random, but to make sure that we tried each of them I changed it so optionally you can specify the column:

```scheme
; Add water to the top row (randomly if column is #f)
(define (drip p [column #f])
  ; Copy the old puddle
  (define new-p
    (puddle (for/vector ([row (in-vector (puddle-data p))])
              (for/vector ([col (in-vector row)])
                col))))

  ; Insert at a specified location or randomly
  (define r (sub1 (puddle-height p)))
  (cond
    [column
     (puddle-set!? new-p r column 'water)]
    [else
     (let/ec break
       (for ([c (in-list (shuffle (range (puddle-width p))))])
         (when (puddle-set!? new-p r c 'water)
           (break))))])

  new-p)
```

Cool. So what do we need to make this actually run a simulation? Well, first you could write everything manually. But that won't (easily) let you visualize it. Luckily, there is a perfect solution to running and visualizing a simulation: {{< doc racket "2hdtp/universe" >}}. Specifically, the {{< doc racket "big-bang" >}} function.

```scheme
; Run an entire simulation until steady state
(define (simulate puddle)
  (define previous-states          (make-hash))
  (define (previous-state? puddle) (hash-has-key? previous-states puddle))
  (define (add-state! puddle)      (hash-set! previous-states puddle #t))

  (define potential-drips (shuffle (range (puddle-width puddle))))
  (define stop? #f)

  (big-bang puddle
    [record? "output"]
    [stop-when (λ (puddle) stop?)]
    [on-draw draw-puddle]
    [on-tick
     (λ (puddle)
       (let/ec return
         ; We've not seen the stepped case before, use that
         (define stepped (step puddle))
         (when (and (not (equal? stepped puddle))
                    (not (previous-state? stepped)))
           (add-state! stepped)
           (return stepped))

         ; If we don't have any potential drips left, we've reached steady state
         ; Try inverting first
         (when (null? potential-drips)
           (when (equal? stepped puddle)
             (printf "steady state: ~a\n" (puddle-count puddle 'water))
             (set! stop? #t))

           (return stepped))

         ; Try to drip instead, if we've seen this drip, don't drip here again
         (define dripped (drip puddle (car potential-drips)))
         (when (or (equal? dripped puddle)
                   (previous-state? dripped))
           (set! potential-drips (cdr potential-drips)))

         (return dripped)))]))
```

There are a few other bits here, so let's break it down. First, we have some separate state for the simulation. We want to keep track of every state that we generate, since if we see something that we've already seen before, we know that we can advance. When we get into the `big-bang`, we have four clauses of interest:


* `record?`
* `stop-when`
* `on-draw`
* `on-tick`


`record?` lets us generate GIFs. I'll show one here in a second. `stop-when?` stops the simulation and returns the ending state. `on-draw` is the function used to turn a puddle into an image that `2htdp/universe` can use. Finally, `on-tick` is the meat of the function.

Within `on-tick` we have a series of checks. First, we try to step. If we can't, then the current water has reached a steady state. Unfortunately, we also need to check multiple previous states because it's easily possible for water to alternate between two states given a flat surface.

If both of those conditions are skipped, then we should try to drip. Here, I have a list of the columns (shuffled for appearance) that will each be tried in turn. Once that list is `null?`, we're probably null. Run one last time until steady state so that the water can settle and then count it up.

Finally, if we get this far, try to drip. We know that a state is done if dripping ends up with the same state we've seen before because that means water is no longer settling and instead draining out of the world.

Well, that's that. The only thing we have left is the drawing function: Using the `2htdp/image` library, it's rather straight forward:

```scheme
; Convert a puddle into a pict
(define (draw-puddle p)
  (define (make-row row)
    (apply beside
           (for/list ([col (in-vector row)])
             (rectangle
              (current-block-size) (current-block-size)
              "solid"
              (case col
                [(empty) "white"]
                [(wall)  "black"]
                [(water) "blue"])))))

  (apply above
         (reverse
          (for/list ([row (in-vector (puddle-data p))])
            (make-row row)))))
```

And that's it. I did promise an animated GIF (and `record?` makes that trivial), so here it is:

```scheme
> (parameterize ([current-block-size 25])
    (simulate (make-puddle '(2 5 1 2 3 4 7 7 6))))
```

{{< figure src="/embeds/2013/solution.gif" >}}

```scheme
steady state: 10
(puddle
 '#(#(wall wall wall wall wall wall wall wall wall)
    #(wall wall water wall wall wall wall wall wall)
    #(empty wall water water wall wall wall wall wall)
    #(empty wall water water water wall wall wall wall)
    #(empty wall water water water water wall wall wall)
    #(empty empty empty empty empty empty wall wall wall)
    #(empty empty empty empty empty empty wall wall empty)
    #(empty empty empty empty empty empty empty empty empty)))
```

And there we have it. As always, if you'd like to see the code for today's post, you can do so here: <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/twitter-puddle.rkt">twitter-puddle</a>.

[^1]: Don't worry, I am still intending to post more in the [Making music series]({{< ref "2013-11-09-chapter-2-writings-in-silver.md" >}}), just not today.
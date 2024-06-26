---
title: Clockception
date: 2014-11-04 09:00:00
programming/languages:
- Racket
- Scheme
programming/topics:
- Fractals
- Graphics
---
Let's talk about clocks.

We can draw traditional analog clocks[^1]:

{{< figure src="/embeds/2014/analog.png" >}}

We can draw nice digital clocks:

```
┌─┐  │ │ ─┐ ┌─┐
│ │└─┤    │ │ │
└─┘  │ │ ─┴─└─┘
```

Or we can go downright mad and make clocks out of clocks:

{{< figure src="/embeds/2014/clockception.png" >}}

Even animated!

{{< figure src="/embeds/2014/animated.gif" >}}

<!--more-->

I got the basic idea for this post from <a href="http://io9.com/these-stylish-minimalistic-clocks-let-you-tell-time-wit-1652202065">this post</a> on io9. That first clock ought to look awfully familiar (although theirs looks a bit better). Let's see how we can make one of our own.

First, some basic structure:

```racket
(struct time-data (hour minute second) #:transparent)

(define (time hour minute [second #f])
  (time-data hour minute second))

(define current-size (make-parameter 30))
```

This will represent the times that we are dealing with. I specifically broke the `time-data` structure and `time` function apart, since I wanted to have optional parameters. There is an `#:auto` option for struct fields, but it doesn't quite do what I want. Finally, `current-size` will be the width of each individual analog clock.

Speaking of which, let's draw some basic analog clocks. I went through several different Racket drawing libraries ({{< doc racket "pict" >}}, ({{< doc racket "2htdp/image" >}}, ({{< doc racket "racket/draw" >}}) before finally settling on {{< doc racket "racket/draw" >}}. I'm sure any of them could be used, but I just kept running into odd issues with coordinates.

```racket
; Render a clock at the current-size
(define (analog-clock when)
  (match-define (time-data hour minute second) when)

  (define size (current-size))
  (define target (make-bitmap size size))
  (define dc (new bitmap-dc% [bitmap target]))

  (send dc set-pen "lightgray" 1 'solid)
  (send dc draw-ellipse 0 0 size size)
  (send dc set-pen "black" 1 'solid)

  ; Helper to draw a hand given a radius [0, 1.0] and angle
  ; Angle of 0 is upright, positive angles are clockwise
  (define (draw-hand! r θ)
    (define c (/ size 2))
    (define x (+ c (* 0.5 r size (cos θ))))
    (define y (+ c (* 0.5 r size (sin θ))))
    (send dc draw-line c c x y))

  (draw-hand! 0.8 (+ (* pi 1.5) (* 2 pi (/ minute 60))))
  (draw-hand! 0.7 (+ (* pi 1.5) (* 2 pi (/ hour 12))))

  (and second
       (begin
         (draw-hand! 0.9 (+ (* pi 1.5) (* 2 pi (/ second 60))))))

  target)
```

The basic idea of `racket/draw` is that you have a sort of canvas (`target`) on which you can draw. You then issue a series of commands that either change your state ({{< doc racket "set-pen" >}}) or draw ({{< doc racket "draw-ellipse" >}} and {{< doc racket "draw-line" >}}). I did abstract a little bit the function to create the clock hands: `draw-hand!`, mostly so I wouldn't have to redo the centering offset (`c`, since `0,0` is in the top left, not the center as I'd hoped) and the [[wiki:trigonometry]]() to convert a radius and angle to x and y.

And that's actually all you need to make a basic clock:

```racket
> (analog-clock (time 4 10))
```
{{< figure src="/embeds/2014/analog.png" >}}

Straight forward enough. What's especially neat is that because radians cycle every two 2π rotations, you can put in some crazy times:

```racket
> (analog-clock (time 208 -350))
```
{{< figure src="/embeds/2014/analog.png" >}}

Cool. Okay, next step. Let's figure out how to animate these, so we can transition from one time to another. In this, I had two options. Either I could move as a clock moves (where the minute hand has to move an entire rotation for the hour hand to move 1/12) or independently (such that both hands move at the same speed). Because it's both less code and honestly works better in the final result, I went with the second option:

```racket
; Render a sequence of frames animating a clock spinnging from one time to another
; Hands will always move clockwise but will both move at once (not as a normal clock)
(define (analog-frames α β frames)
  (match-define (time-data α-hour α-minute α-second) α)
  (match-define (time-data β-hour β-minute β-second) β)

  (let ([β-hour   (if (>= β-hour α-hour)     β-hour    (+ β-hour 12))]
        [β-minute (if (>= β-minute α-minute) β-minute (+ β-minute 60))]
        [β-second (and α-second β-second
                       (if (>= β-second α-second) β-second (+ β-second 60)))])

    (for/list ([i (in-range frames)])
      (define frame-multiplier (/ i frames))

      (define hour (+ α-hour (* frame-multiplier (- β-hour α-hour))))
      (define minute (+ α-minute (* frame-multiplier (- β-minute α-minute))))

      (define second
        (and α-second β-second
             (+ α-second (* frame-multiplier (- β-second α-second)))))

      (analog-clock (time hour minute second)))))
```

Basically, we will loop through the frames and interpolate for each frame. The `frame-multiplier` will range evenly from 0 to 1 over the course of the frames. Also, the `let` block setting `β-hour` etc is to make sure that the clocks rotate clockwise. Since the second (`β`) value will always be higher, we always rotate right.

Okay, next let's switch gears and make some digital clocks. Since the eventual end goal was to make clocks out of clocks, I wanted a nice blocky font, built out of only a few different pieces. That way we could animate it more easily. Luckily the Unicode [[wiki:box-drawing characters]]() will do exactly what we need:

I went with a 3x3 character map for each letter:

```racket
(define digits
  (vector "┌─┐│ │└─┘" ; 0
          "─┐  │ ─┴─" ; 1
          " ─┐┌─┘└──" ; 2
          "──┐ ─┤──┘" ; 3
          "  │└─┤  │" ; 4
          "┌─ └─┐──┘" ; 5
          "│  ├─┐└─┘" ; 6
          "──┐  │  │" ; 7
          "┌─┐├─┤└─┘" ; 8
          "┌─┐└─┤  │" ; 9
          " │     │ " ; delimiter
          " ○     ○ "))
```

If you straighten them out, you have things like this for 5 for example:

```
┌─
└─┐
──┘
```

They're not perfect, but I think they have a certain sort of charm.

Putting that all together, we can loop across all of the digits in the final clock and then each character that makes them up:

```racket
; Render a digital clock using ascii bar graphics
(define (digital-clock when)
  (match-define (time-data hour minute second) when)

  (string-join
   (for/list ([line-index (in-range 3)])
     (list->string
      (for*/list ([digit
                   (in-list
                    (append (list (if (< hour 10) 0 (quotient hour 10))
                                  (remainder hour 10)
                                  10
                                  (if (< minute 10) 0 (quotient minute 10))
                                  (remainder minute 10))
                            (if second
                                (list 10
                                      (if (< second 10) 0 (quotient second 10))
                                      (remainder second 10))
                                (list))))]
                  [char-index (in-range 3)])

        (define str (vector-ref digits digit))
        (define char (string-ref str (+ char-index (* line-index 3))))

        char)))
   "\n"))
```

It's a bit ugly, but the bulk of the code is to make sure that we have enough digits for numbers less than 10. I bet I could do something nice with string formatting, but it works well enough. An example:

```racket
> (digital-clock (time 4 10))
"┌─┐  │ │ ─┐ ┌─┐\n│ │└─┤    │ │ │\n└─┘  │ │ ─┴─└─┘"
```

Oops.

```racket
> (display (digital-clock (time 4 10)))
┌─┐  │ │ ─┐ ┌─┐
│ │└─┤    │ │ │
└─┘  │ │ ─┴─└─┘
```

Much better.

Okay, now we're at the point of no return. How do we turn a digital clock with that 3x3 font into smaller clocks?

First, we need a map of the bar characters to times:

```racket
; Convert the bar images used back into clocks
(define bar->clock
  (hash #\└ (time 3 0 0)
        #\┘ (time 9 0 0)
        #\┼ (time 6 0 30)
        #\─ (time 3 45 45)
        #\┴ (time 6 45 15)
        #\├ (time 3 0 30)
        #\┤ (time 9 30 0)
        #\┬ (time 6 15 45)
        #\┌ (time 3 30 30)
        #\┐ (time 9 30 30)
        #\│ (time 12 30 30)
        #\○ #f
        #\space #f))
```

These could probably use a little more tuning. But what this does allow us to make is a very simple function to make a clock out of clocks:

```racket
(define timeless (make-parameter (time 12 0 0)))

; Make a clock out of clocks!
(define (clock-clock when)
  (define chars (digital-clock when))
  (define empty-frame (analog-clock (timeless)))

  (define rows
    (for/list ([line (in-list (string-split chars "\n"))])
      (for/list ([char (in-string line)])
        (cond
          [(hash-ref bar->clock char) => analog-clock]
          [else empty-frame]))))

  (apply above (map (curry apply beside) rows)))
```

In use:

```racket
> (clock-clock (time 4 10))
```
{{< figure src="/embeds/2014/clockception.png" >}}

That right there is actually one of the parts of programming I love the most. Where you write a small pile of functions, each of which does one specific piece and then when you finally get to the big overall algorithm... bam. Simple.

But... back to being a little more complicated. How do we do the transition from one `clock-clock` to another? It would be nice if we could use the previous function, but we really can't. A similar idea will work though:

```racket
; Animate a clock of clocks turning from one time to another
(define (tick-tock α β frames)
  (define α-chars (digital-clock α))
  (define β-chars (digital-clock β))

  (define rows*
    (for/list ([α-line (in-list (string-split α-chars "\n"))]
               [β-line (in-list (string-split β-chars "\n"))])
      (for/list ([α-char (in-string α-line)]
                 [β-char (in-string β-line)])
        (analog-frames (or (hash-ref bar->clock α-char) (timeless))
                       (or (hash-ref bar->clock β-char) (timeless))
                       frames))))

  (for/list ([i (in-range frames)])

    (define rows
      (for/list ([row (string-split α-chars "\n")]
                 [row-index (in-naturals)])
        (for/list ([char-index (in-range (string-length row))])
          (list-ref (list-ref (list-ref rows* row-index) char-index) i))))

    (apply above (map (curry apply beside) rows))))
```

Basically, we have two steps. First we define `rows*` by generating each of the subclocks for each of the intermediate times. Then, that last is in the wrong order (indexed by row, column, then frame, rather than frame, row, then column) so we unpack it and put it back together. This is pretty terribly inefficient, but there will only ever be 3 rows and up to 20 columns, so it's not that bad.

With that, we can make simple animations:

```racket
> ; Fix bitmaps so that big-bang / run-movie / etc can render them
> (define (fix img) (rotate 0 img))
> (run-movie 0.1 (tick-tock (time 7 59) (time 8 0) 56))
```

{{< figure src="/embeds/2014/animated.gif" >}}

I really wish that `fix` wasn't necessary, but for whatever reason, {{< doc racket "big-bang" >}} / {{< doc racket "run-movie" >}} / et al don't like {{< doc racket "bitmap%" >}}s. So it goes.

On the other hand though, {{< doc racket "run-movie" >}} is really cool. I've been doing things like this with {{< doc racket "big-bang" >}} and the `stop-when` parameter, but this just needs a list of images and stops automatically. Another tool for my toolchest!

Okay, one more step. I know I just said {{< doc racket "run-movie" >}} is the new shiny, but let's step back to {{< doc racket "big-bang" >}} for a second. Given that we have a clock made of clocks, what would it take to actually render it in real time?

```racket
; Make a tick-tock real time clock
(define (tick-tock-real-time-clock #:12-hour? [12-hour? #f])
  ; Get the current time in hours/minutes/seconds
  (define (now)
    (define date (current-date))
    (time (date-hour date) (date-minute date) #f))

  ; Generate a list of frames for the next transition
  ; Note: The big bang clock is supposed to tick 28 times per second
  (define (transition-frames)
    (match-define (time-data hour minute _) (now))

    (define next-minute (remainder (+ minute 1) 60))
    (define next-hour (remainder (if (= next-minute 60) (+ hour 1) hour) (if 12-hour? 12 24)))

    (tick-tock (time hour minute)
               (time next-hour next-minute)
               56)) ; Note: The big bang clock is supposed to
                    ; tick 28 times per second

  (big-bang (list (now) (transition-frames))
    [on-tick
     (λ (state)
       (match-define (list old-time frames) state)
       (define new-time (now))
       (cond
         ; We've advanced to the new time, jump ahead!
         [(not (equal? old-time new-time))
          (list new-time (transition-frames))]
         ; Freeze if we only have one frame left
         [(null? (rest frames))
          state]
         ; Otherwise, advance one frame
         [else
          (list old-time (rest frames))]))]
    [to-draw
     (λ (state)
       (match-define (list old-time frames) state)
       (fix (first frames)))]))
```

Now that is a cool function. Basically, each minute we will generate the frames that will be used by the transition. Since `big-bang` runs at 28 frames per second, the 56 frames will takes 2 seconds to animate. Each minute, the next transition will be generated and then ticked down one frame at a time until only one is left, at which point we will just wait. Neat!

Originally I had it rendering seconds as well, but it was just a little bit too jittery. So minutes it is! I can't really do this thing justice in a gif (it actually looks just like `tick-tock` above, just with the current time), but it's still pretty cool.

And... that's it. Clocks made of clocks. Who would have thought? As always, the full code is available on GitHub. Check it out: <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/clockception.rkt">clockception.rkt</a>

[^1]: I wonder what percentage of people can still read these? Takes me a bit longer than it used to...
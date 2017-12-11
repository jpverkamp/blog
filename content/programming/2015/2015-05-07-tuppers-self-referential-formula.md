---
title: Tupper's self-referential formula
date: 2015-05-07
programming/languages:
- Racket
programming/topics:
- Graphics
- Mathematics
---
Quick post today. Let's implement {{< wikipedia "Tupper's self-referential formula" >}} in Racket!

{{< latex >}}\frac{1}{2} < \left \lfloor mod \left ( \left \lfloor \frac{y}{17} 2^{-17 \lfloor x \rfloor - mod(\lfloor y \rfloor, 2)} \right \rfloor, 2 \right ) \right \rfloor{{< /latex >}}

```racket
(tupper 960939379918958884971672962127852754715004339660129306651505519271702802395266424689642842174350718121267153782770623355993237280874144307891325963941337723487857735749823926629715517173716995165232890538221612403238855866184013235585136048828693337902491454229288667081096184496091705183454067827731551705405381627380967602565625016981482083418783163849115590225610003652351370343874461848378737238198224849863465033159410054974700593138339226497249461751545728366702369745461014655997933798537483143786841806593422227898388722980000748404719)
```

{{< figure src="/embeds/2015/tupper.png" >}}

That's the result of graphing the above function at a point rather far away from the origin. Specifically, where `y` is around that crazy big number. Look familiar?

<!--more-->

The basic idea behind the formula is that it can encode any arbitrary bitmap (so long as it's black and white and only 106x17 pixels). Essentially under the hood everything is in base 17. First, let's fairly directly translate the original formula into Racket:

```racket
; Tupper's "self-referential" formula
; Encodes a bitmap as an integer
(define (tupper k)
  (flomap->bitmap
   (build-flomap*
    1 106 17
    (λ (x y)
      (set! y (+ y k))
      (set! x (- 105 x))
      (cond
        [(< 1/2 (floor (mod (* (floor (/ y 17)) (expt 2 (- (* -17 (floor x)) (mod (floor y) 17)))) 2)))
         (vector 0)]
        [else
         (vector 1)])))))
```

One amusing caveat that we have to deal with here is that `modulus` doesn't work on numbers this large. So instead, we're going to have to do it manually:

```racket
; Modulus that will work with really large numbers
(define (mod a b)
  (define q (floor (/ a b)))
  (define r (- a (* b q)))
  r)
```

Whee!

Another neat trick I was playing with is "rendering" the image by adding one digit at a time (in base 10, so it's mostly noise):

```racket
(define (render-to target)
  (define str-target (number->string target))
  (define str-buffer (make-string (string-length str-target) #\0))

  (for/list ([i (in-range (sub1 (string-length str-target)) -1)])
    (string-set! str-buffer i (string-ref str-target i))
    (tupper (string->number str-buffer))))

> (write-animated-gif
   (render-to 960939379918958884971672962127852754715004339660129306651505519271702802395266424689642842174350718121267153782770623355993237280874144307891325963941337723487857735749823926629715517173716995165232890538221612403238855866184013235585136048828693337902491454229288667081096184496091705183454067827731551705405381627380967602565625016981482083418783163849115590225610003652351370343874461848378737238198224849863465033159410054974700593138339226497249461751545728366702369745461014655997933798537483143786841806593422227898388722980000748404719)
   5
   "tupper.gif"
   #:last-frame-delay 50)
```

{{< figure src="/embeds/2015/tupper.gif" >}}

If you look carefully, you'll occasionally see flashes of the final image being rendered. This happens whenever the base-10 numbers that we're adding line up with the base-17 encoding.

I'm not sure it's particularly useful for anything, but I found it amusing.

Code: <a href="https://github.com/jpverkamp/small-projects/blob/master/blog/tupper.rkt">tupper.rkt</a>

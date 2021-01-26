#lang racket

(require (prefix-in image: 2htdp/image))

(struct point (x y) #:transparent)
(struct circle (center radius) #:transparent)
(struct line (p1 p2) #:transparent)
(struct star (center inner-radius outer-radius points) #:transparent)

(struct anchor (x y) #:transparent)
(struct rune (shapes) #:transparent)

(define SHAPES '(circle line line line line))
;(define SHAPES '(circle))
(define MAX-SIZE 100)

; Terrible way to randomly choose something from a list
(define (choose ls)
  (list-ref ls (random (length ls))))

; Add a new shape to the current rune
(define (extend r)
  (define old-shapes (rune-shapes r))
  (define new-shape
    (case (choose SHAPES)
      [(point)
       (random-point (choose old-shapes))]
      [(circle)
       (circle (random-point (choose old-shapes))
               (* (random) (/ MAX-SIZE 2)))]
      [(star)
       (star (random-point (choose old-shapes))
             (* (random) (/ MAX-SIZE 2))
             (* (random) (/ MAX-SIZE 2))
             (+ 3 (random 4)))]
      [(line)
       (line (random-point (choose old-shapes))
             (random-point (choose old-shapes)))]))
  (rune (cons new-shape old-shapes)))
  
; Get a random point on a given shape
(define (random-point shape)
  (match shape
    [(point x y) (point x y)]
    [(anchor x y) (point x y)]
    [(circle (point x y) radius)
     (define angle (* 2 pi (random)))
     (point (+ x (* (cos angle) radius))
            (+ y (* (sin angle) radius)))]
    [(star (point x y) r1 r2 n)
     (point x y)]
    [(line (point x1 y1) (point x2 y2))
     (cond
       [(= x1 x2)
        (point x1 (+ y1 (* (- y2 y1) (random))))]
       [else
        (define slope (/ (- y2 y1) (- x2 x1)))
        (define x (+ (* (- x1 x2) (random)) x1))
        (define y (+ (* (- x1 x) slope) y1))
        (point x y)])]))

; Render a rune
(define (render rune)
  (for/fold ([current-scene (image:empty-scene MAX-SIZE MAX-SIZE)])
            ([shape (in-list (rune-shapes rune))])
    (match shape
      [(anchor x y)
       current-scene]
      [(point x y)
       (image:place-image
        (image:circle 3 "solid" "black")
        x y
        current-scene)]
      [(circle (point x y) radius)
       (image:place-image
        (image:circle radius "outline" "black")
        x y
        current-scene)]
      [(star (point x y) r1 r2 points)
       (image:place-image
        (image:radial-star points r1 r2 "outline" "black")
        x y
        current-scene)]
      [(line (point x1 y1) (point x2 y2))
       (image:scene+line
        current-scene
        x1 y1
        x2 y2
        "black")])))

; Generate a rune of the given complexity
(define (generate complexity)
  (define base (anchor (/ MAX-SIZE 2) (/ MAX-SIZE 2)))
  
  (for/fold ([current-rune (rune (list base))])
            ([i (in-range complexity)])
    (extend current-rune)))

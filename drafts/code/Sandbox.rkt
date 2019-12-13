#lang rackjure

; Run a series of expressions, return the first non-void result
; If all results are void, return nothing
(define-syntax first-non-void
  (syntax-rules ()
    [(_) (void)]
    [(_ body body* ...)
     (let ([result (if (procedure? body) (body) body)])

       (if (eq? (void) result)
           (first-non-void body* ...)
           result))]))

; Define a custom behavior by running a series of rules
; The first non-void result is returned
; Can be paramaterized
(define-syntax define-behavior
  (syntax-rules ()
    [(_)
     (thunk #f)]
    [(_ (name arg* ...) body* ...)
     (define (name arg* ...) (thunk (first-non-void body* ...)))]
    [(_ name body* ...)
     (define (name) (first-non-void body* ...))]))

; Used to define rules on particles, this is where particle field definitions go
; [solid] if the particle should not rise or fall
; [density {n}] if the particle should rise (negative density) or fall (positive density)
; [update {rule ...}] rules to update this particle, uses the same behavior as above
(define-syntax set-rule!
  (syntax-rules (density solid update)
    [(_ h solid)
     (hash-set! h 'solid #t)]
    [(_ h density value)
     (hash-set! h 'density value)]
    [(_ h update rule* ...)
     (hash-set! h 'update (thunk (first-non-void rule* ...)))]))

; The default particule if no other rules are applied
(define default-particle
  (hash 'solid   #f
        'density 0
        'update  void))

; Define a new particle with any properties overriding the defaults
(define-syntax define-particle
  (syntax-rules ()
    [(_ name [key* val** ...] ...)
     (define name
       (let ([thing (hash-copy default-particle)])
         (set-rule! thing key* val** ...) ...
         thing))]))

(define (count which) (random 8))
(define (at xd yd)    'empty)

; ----- other -----

(define-behavior (*decays* to)
  (when (zero? (random 100)) to))

; ----- burning things -----

(define-behavior *burns*
  (when (>= (count 'fire) 1) 'fire))

(define-particle smoke
  [density -1]
  [update
   (*decays* #f)])

(define-particle fire
  [update
   (*decays* 'smoke)])

; ----- growing things -----

(define-behavior *grows*
  (when (>= (count 'dirt) 1) 'plant)
  (when (>= (count 'plant) 1) 'plant))

(define-particle dirt
  [solid])

(define-particle plant
  [solid]
  [update *burns*])

(define-particle water
  [density 1]
  [update *grows*])

(define-particle oil
  [density 0.5]
  [update *burns*])


; ######################### ######################### #########################

(require 2htdp/image
         2htdp/universe
         images/flomap)

(struct sand (rules colors grid) #:transparent)
(struct grid (width height data) #:transparent)

(define (grid-ref g x y)
  (match-define (grid width height data) g)
  (if (and (<= 0 x (- width 1))
           (<= 0 y (- height 1)))
      (vector-ref data (+ x (* y width)))
      #f))

(define (grid-generator width height f)
  (grid width height
        (for*/vector ([x (in-range width)]
                      [y (in-range height)])
          (f x y))))

(define (update s)
  (match-define (sand rules colors g) s)
  (match-define (grid width height data) g)

  ; Update a given point based on that point's rules
  (define (update-each x y)
    (cond
      [(hash-ref rules (grid-ref g x y))
       => (λ (rule)
            ; Get the neighbor of a given type
            (define (at xd yd)
              (grid-ref g (+ x xd) (+ y yd)))

            ; Count neighbors of a given type
            (define (count type)
              (+ (if (eq? type (at -1 -1)) 1 0)
                 (if (eq? type (at -1  0)) 1 0)
                 (if (eq? type (at -1  1)) 1 0)
                 (if (eq? type (at  0 -1)) 1 0)
                 (if (eq? type (at  0  1)) 1 0)
                 (if (eq? type (at  1 -1)) 1 0)
                 (if (eq? type (at  1  0)) 1 0)
                 (if (eq? type (at  1  1)) 1 0)))

            ; Run the function, this will return the new particle type
            (rule count at))]
      [else
       #f]))

  (sand rules colors (grid-generator width height update-each)))

(define (render s #:scale [scale-multiplier 1])
  (match-define (sand rules colors g) s)
  (match-define (grid width height data) g)

  (scale
   scale-multiplier
   (flomap->bitmap
    (build-flomap*
     3 width height
     (λ (x y)
       (hash-ref colors (grid-ref g x y)))))))

(define (simulate s)
  (big-bang s
    [on-tick (λ (s) (update s))]
    [to-draw (λ (s) (render s #:scale 2))]))

#;(simulate
 (sand (hash 'alive (λ (count at) (if (<= 2 (count 'alive) 3) 'alive 'dead))
             'dead  (λ (count at) (if (=  3 (count 'alive)  ) 'alive 'dead)))
       (hash 'alive '#(1 1 1)
             'dead  '#(0 0 0))
       (grid-generator 50 50 (λ _ (if (zero? (random 4)) 'alive 'dead)))))

#;(simulate
 (sand (hash 'dead  (λ _ (if (zero? (random 50)) 'spawn 'dead))
             'spawn (λ (count at) (if (= 6 (count 'dead)) 'alive 'dead))
             'alive (λ (count at) (if (= 2 (count 'alive)) 'alive 'dead)))
       (hash 'dead  '#(0 0 0)
             'spawn '#(1 0 0)
             'alive '#(1 1 1))
       (grid-generator 50 50 (λ _ 'dead))))

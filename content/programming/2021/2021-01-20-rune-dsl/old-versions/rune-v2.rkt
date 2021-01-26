#lang racket

(require (prefix-in image: 2htdp/image))
(require racket/trace
         xml)

(define symbols
  (hash 'alchemical '(#x1F700 #x1F773)
        'egyptian   '(#x13000 #x1342E)
        'hebrew     '(#x05D0  #x05EA)
        'geometric  '(#x25A0  #x25FF)
        'runic      '(#x16A0  #x16EA)
        'moon       '(#x1F311 #x1F320)))

; circle
; circle text
; star
; arrow / ray
; polygon

(define CSS
  "
svg polygon, svg circle {
  fill: none;
  stroke: black;
}
svg text {
  dominant-baseline: middle;
  text-anchor: middle;
}
")

(struct Point (x y) #:transparent)

(struct Rune (children) #:transparent)
(struct Circle () #:transparent)
(struct FilledCircle () #:transparent)
(struct Scaled (scale children) #:transparent)
(struct Spaced (scale children) #:transparent)
(struct Star (points step) #:transparent)
(struct Polygon (points) #:transparent)
(struct Symbol (symbol) #:transparent)

(define (point-string ls)
  (string-join
   (for/list ([p (in-list ls)])
     (match-define (Point x y) p)
     (~a x "," y))))

(define (render el [size 100])
  (define radius (/ size 2))
  (match el
    [(Rune layers)
     `(g () 
         ,@(for/list ([layer (in-list layers)])
            (render layer size)))]

    [(Scaled scale layers)
     `(g ()
         ,@(for/list ([layer (in-list layers)])
             (render layer (* scale size))))]

    [(Circle)
     `(circle ([cx "0"] [cy "0"] [r ,(~a radius)]))]

    [(FilledCircle)
     `(circle ([cx "0"] [cy "0"] [style "fill:white"] [r ,(~a radius)]))]
    
    [(Polygon n)
     (define points
       (for/list ([i (in-range n)])
         (define θ (* i (/ (* 2 pi) n)))
         (define x (* radius (sin θ)))
         (define y (* -1 radius (cos θ)))
         (Point x y)))
     `(polygon ([points ,(point-string points)]))]
      
    [(Star n skip)
     (define points
       (for/list ([i (in-range n)])
         (define θ (* i skip (/ (* 2 pi) n)))
         (define x (* radius (sin θ)))
         (define y (* -1 radius (cos θ)))
         (Point x y)))
     `(polygon ([points ,(point-string points)]))]

    [(Spaced scale ls)
     (define n (length ls))
     `(g ()
         ,@(for/list ([i (in-range n)]
                      [el (in-list ls)])
             (define θ (* i (/ (* 2 pi) n)))
             (define x (* radius (sin θ)))
             (define y (* -1 radius (cos θ)))
             `(g ([transform ,(~a "translate(" x " " y ") rotate(" (radians->degrees θ) ")")])
                 ,(render el (* scale size)))))]

      [(Symbol c)
       `(text ([x "0"] [y "0"] [font-size ,(~a (/ size 4)) #;,(~a size "%")]) ,c)]))

(with-output-to-file "rune.html"
  #:exists 'replace
  (thunk
   (display "<html><head><style>")
   (display CSS)
   (display "</style><body>")
   (write-xexpr
    `(svg
      ([viewBox "-100 -100 200 200"])
      ,(render
        (Rune (list
               (Circle)
               (Scaled 0.9 (list (Circle)))
               (Star 7 2)
               (Spaced 0.2 (for/list ([i (in-range 7)])
                             (Rune (list (FilledCircle)
                                         (Symbol (~a (integer->char (+ #x1F700 i 1))))))))
               (Scaled 0.6 (list (Circle)
                                 (Star 7 3)
                                 (Spaced 0.2 (for/list ([i (in-range 7)])
                                               (Rune (list
                                                      (FilledCircle)
                                                      (Symbol (~a (integer->char (+ #x05D0 i 1))))))))
                                 (Scaled 0.5 (list (FilledCircle)))
                                 (Scaled 0.4 (list (FilledCircle)
                                                   (Symbol (~a (integer->char #x13000)))))))
               )))))
   (display "</body></html>")))

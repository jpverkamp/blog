#lang racket

(require racket/random
         xml)

(define symbols
  (hash 'alchemical '(#x1F700 #x1F773)
        'egyptian   '(#x13000 #x1342E)
        'hebrew     '(#x05D0  #x05EA)
        'geometric  '(#x25A0  #x25FF)
        'runic      '(#x16A0  #x16EA)))

(define (rune->svg rune [size 100])
  (define env (make-base-namespace))
  (define (val code) (eval code env))
  
  `(svg
    ([viewBox ,(~a "-" size " -" size " " (* 2 size) " " (* 2 size))])
    ,(let loop ([rune rune] [size size])
       (define radius (/ size 2))
       (match rune
         ; Just a general container usually used as the root
         [`(Rune . ,children)
          `(g ([class "rune"])
              ,@(for/list ([child (in-list children)])
                  (loop child size)))]
      
         ; Simple circles, might be filled or not
         [`(Circle)
          `(circle ([cx "0"] [cy "0"] [r ,(~a radius)]))]
         [`(Circle filled)
          `(circle ([cx "0"] [cy "0"] [style "fill:white"] [r ,(~a radius)]))]

         ; Stars, polygons are a subset of stars with step = 1
         [`(Polygon ,n) (loop `(Star ,(val n) 1) size)]
         [`(Polygon filled ,n) (loop `(Star filled ,(val n) 1) size)]
         [`(Star ,n ,step)
          (let ([n (val n)] [step (val step)])
            `(polygon ([points ,(string-join
                                 (for/list ([i (in-range n)])
                                   (define θ (* i step (/ (* 2 pi) n)))
                                   (define x (* radius (sin θ)))
                                   (define y (* -1 radius (cos θ)))
                                   (~a x "," y))
                                 " ")])))]
         ; Fix copy/paste
         [`(Star filled ,n ,step)
          (let ([n (val n)] [step (val step)])
            `(polygon ([style "fill:white"]
                       [points ,(string-join
                                 (for/list ([i (in-range n)])
                                   (define θ (* i step (/ (* 2 pi) n)))
                                   (define x (* radius (sin θ)))
                                   (define y (* -1 radius (cos θ)))
                                   (~a x "," y))
                                 " ")])))]

         ; A wrapper that rescales child runes
         [`(Scaled ,scale . ,children)
          `(g ([class "scaled"])
              ,@(for/list ([child (in-list children)])
                  (loop child (* scale size))))]

         ; Render a list of children evenly spaced in a circle
         
         ; - mode 1: (Spaced 0.2 i 7 child ...) to generate the list in place
         ; Variable will be bound to the index of that child
         [`(Spaced ,(? number? scale) ,variable ,count . ,children)
          (let ([count (val count)])
            `(g ([class "spaced-generated"])
                ,@(for*/list ([i (in-range count)]
                              [child (in-list children)])
                    (define θ (* i (/ (* 2 pi) count)))
                    (define x (* radius (sin θ)))
                    (define y (* -1 radius (cos θ)))
                    (eval `(define ,variable ,i) env)
                    `(g ([class "spaced-generated-child"]
                         [transform ,(~a "translate(" x " " y ") rotate(" (radians->degrees θ) ")")])
                        ,(loop child (* scale size))))))]

         ; - mode 2: (Spaced 0.2 (list child ...) if you already have a list
         [`(Spaced ,(list children ...))
          (loop `(Spaced 1.0 ,(list children)) size)]
         
         [`(Spaced ,(? number? scale) ,(list children ...))
          (let ([count (length children)])
            `(g ([class "spaced-list"])
                ,@(for/list ([i (in-range count)]
                             [child (in-list children)])
                    (define θ (* i (/ (* 2 pi) count)))
                    (define x (* radius (sin θ)))
                    (define y (* -1 radius (cos θ)))
                    `(g ([class "spaced-list-child"]
                         [transform ,(~a "translate(" x " " y ") rotate(" (radians->degrees θ) ")")])
                        ,(loop child (* scale size))))))]

         ; Render symbols, these can by dynamically generated
         [`(Symbol ,code)
          `(text ([x "0"] [y "0"] [font-size ,(~a (/ size 4))])
                 ,(~a (val code)))]

         ; Render arrows, a line with a rune at the end
         [`(Arrow ,(? number? head-scale) . ,children)
          (let ([count (length children)]
                [head-size (* radius head-scale)])
            `(g ([class "arrow"])
                (line ([x1 "0"] [y1 ,(~a radius)]))
                ,@(for/list ([i (in-range count)]
                             [child (in-list children)])
                    `(g ([class "arrow-child"]
                         ,@(if (> count 1)
                               `([transform ,(~a "translate(0 " (* i (/ head-size (- count 1))) ")")])
                               `()))
                        ,(loop child (/ head-size count))))))]
         
         [`(Arrow . ,children)
          (loop `(Arrow 1.0 . ,children) size)]

         ; A simple side to side bar (mostly useful for arrows)
         ; Can pass (Bar left) or (Bar right) to do half bars
         [`(Bar left) `(Line ([x1 ,(~a "-" radius)]))]
         [`(Bar right) `(Line ([x1 ,(~a radius)]))]
         [`(Bar)
          `(g ()
              (Line ([x1 ,(~a "-" radius)]))
              (Line ([x1 ,(~a radius)])))]

         ; Horizontal dots (mostly for arrows)
         [`(Dots ,n)
          `(g)]

         ; Fork (mostly for arrows]
         [`(Fork ,n)
          `(g)]
         [`(Fork ,(list children ...))
          `(g)]

         ; Render cresent moons, phase is -1 (full) waning to 0 (new) and waxing to 1 (full again)  
         [`(Cresent ,phase)
          `(g)]

         ; Render 

         ))))

(define (random-arrow)
  `(Arrow
    ,@(for/list ([i (in-range (random 1 5))])
        (case (random 10)
          [(0) (random-rune)]
          [(1 2) `(Bar left)]
          [(3 4) `(Bar right)]
          [(5 6) `(Bar)]
          [(7 8) `(Polygon filled 3)]
          [(9) `(Circle filled)]))))

(define (random-rune [complexity 3])
  `(Rune
    (Circle)
    ,@(for/list ([i (in-range complexity)])
        (case (random 10)
          [(0) `(Circle)]
          [(1) `(Circle filled)]
          [(2) `(Polygon ,(random 2 10))]
          [(3) `(Star ,(random 2 10) (random 2 10))]
          [(4) `(Scaled ,(random) ,(random-rune (- complexity 1)))]
          [(5 6)
           `(Spaced ,(/ (random) 2) ,(for/list ([i (in-range 2 10)])
                                       (random-rune (- complexity 1))))]
          [(7 8)
           `(Symbol ,(let ([alphabet (random-ref (hash-keys symbols))])
                       (match-define (list lo hi) (hash-ref symbols alphabet))
                       (integer->char (+ lo (random (+ (- hi lo) 1))))))]
          [(9) (random-arrow)]))))

(define (write-rune filename rune)
  (with-output-to-file filename
    #:exists 'replace
    (thunk
     (display "<html><head><style>")
     (display   "
svg polygon, svg circle, svg line {
  fill: none;
  stroke: black;
}
svg text {
  dominant-baseline: middle;
  text-anchor: middle;
}
")
     (display "</style><body>")
     (write-xexpr (rune->svg rune))
     (display "</body></html>"))))

#;(write-rune
 "rune.html"
 `(Rune
   (Circle)
   (Spaced 1.0 i 7
           (Arrow
            (Polygon filled (+ i 3))
            (Bar)
            (Star filled (+ i 3) 2)))))

#;(write-rune
 "vegvisir.html"
 `(Rune
   (Spaced
    ((Arrow 0.5 (Bar) (Bar) (Bar) (Fork 3))
     (Arrow 0.5 (Crescent -0.5) (Crescent 0.5) (Fork 3))
     (Arrow 0.5 (Crescent -0.5) (Bar) (Crescent 0.5) (Fork 3))
     (Arrow 0.5 (Bar) (Bar) (Bar) (Fork 3))
     (Arrow 0.5
            (Bar) (Bar)
            (Fork (list
                   (Arrow 0.5 (Bar) (Bar))
                   (Rune)
                   (Arrow 0.5 (Bar) (Bar))))
            (Fork 3)
            (Bar))
     (Arrow 0.5 (Crescent -0.5) (Bar) (Fork 3) (Bar) (Bar))
     (Arrow 0.25 (Fork 5))
     (Arrow 0.5 (Crescent -0.5) (Fork 3) (Bar) (Circle))))))
                 
                                       

#;(write-rune
 "rune.html"
 `(Rune
   (Circle)
   (Scaled 0.9 (Circle))
   (Star 7 2)
   (Spaced 0.2
           ,(for/list ([i (in-range 7)])
              `(Rune
                (Circle filled)
                (Symbol ,(integer->char (+ #x16A0 i))))))
   (Scaled 0.6
           (Circle)
           (Star 7 3)
           (Spaced 0.2 i 7
                   (Circle filled)
                   (Spaced 0.2 j i (Circle filled))
                   (Symbol (integer->char (+ #x05D0 i 1))))
           (Scaled 0.3
                   (Circle filled)
                   (Symbol (integer->char #x13000))))))

#;(write-rune "random.html" (random-rune))
 
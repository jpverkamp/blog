#lang racket

; http://www.weitz.de/einstein.html

(struct property (key vals))
(struct puzzle (properties rules))

(define mouse
  (puzzle
   '((mouse  (mickey minny mighty))
     (cheese (emmental gouda brie))
     (show   (seinfeld simpsons er)))
   '((== (mouse mickey) (cheese gouda))
     (== (mouse mighty) (show er))
     (@@ (show seinfeld) 0)
     (<> (mouse mickey) (mouse mighty) 2)
     (<< (cheese brie) (show simpsons) 0 3))))

(define einstein
  (puzzle
   '((nation    (british swedish norwegian german danish))
     (house     (red green yellow blue white))
     (animal    (dog horse cat bird fish))
     (cigarette (marlboro winfield rothmans pallmall dunhill))
     (drink     (tea coffee milk beer water)))
   '((== (cigarette pallmall) (drink milk))
     (== (cigarette winfield) (drink beer))
     (== (house green) (drink coffee))
     (== (nation swedish) (animal dog))
     (== (nation british) (house red))
     (== (nation german) (cigarette rothmans))
     (== (nation danish) (drink tea))
     (@@ (drink milk) 2)
     (@@ (nation norwegian) 0)
     (<< (house green) (house white))
     (<> (cigarette marlboro) (animal cat) 1)
     (<> (cigarette dunhill) (animal horse) 1)
     (<> (cigarette marlboro) (drink water) 1)
     (<> (nation norwegian) (house blue) 1))))

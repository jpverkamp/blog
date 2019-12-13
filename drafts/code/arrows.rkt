#lang racket

; https://www.reddit.com/r/dailyprogrammer/comments/2m82yz/20141114_challenge_188_hard_arrows_and_arrows/

(require pict)

(struct grid (width height data) #:transparent)
(struct node (direction group) #:transparent #:mutable)
(struct point (x y) #:transparent)

; Read in a square grid of ^v<> characters into a grid
(define (read-grid [in (current-input-port)])
  (define raw-data
    (for/list ([line (in-lines in)] #:break (equal? "" line))
      (map string->symbol (map string (string->list line)))))
  
  (when (or (null? raw-data) (null? (first raw-data)))
    (error 'read-grid "must have at least one row/column"))

  (when (not (apply = (map length raw-data)))
    (error 'read-grid "grid must be square"))
  
  (grid (length (first raw-data))
        (length raw-data)
        (for*/vector ([row (in-list raw-data)] [col (in-list row)])
          (node col #f))))

; Better than remainder for grid references
(define (mod a b)
  (let loop ([a a])
    (cond
      [(<  a 0) (loop (+ a b))]
      [(>= a b) (loop (- a b))]
      [else     a])))

; Return the node at a given point in a grid 
(define (grid-ref g p)
  (match-define (grid width height data) g)
  (match-define (point x y) p)
  (vector-ref data (+ (* (mod y height) width) (mod x width))))

; What is the next point on this path?
(define (next g p)
  (match-define (point x y) p)
  (case (node-direction (grid-ref g p))
    [(^) (point x (- y 1))]
    [(v) (point x (+ y 1))]
    [(<) (point (- x 1) y)]
    [(>) (point (+ x 1) y)]))

; Trace the path from a given point until either a cycle or another group
(define (trace! g p group count)
  (match-define (point x y) p)
  
  (let loop ([p p] [seen '()])
    (cond
      [(member p seen)
       (define cycle (member p (reverse seen)))
       (for ([p (in-list cycle)])
         (set-node-group! (grid-ref g p) group))
       #t]
      [(node-group (grid-ref g p))
       (for ([p (in-list seen)])
         (set-node-group! (grid-ref g p) 0))
       #f]
      [else
       (define np (next g p))
       (loop np (cons p seen))])))

; Trace all paths within a given grid
(define (trace-all! g)
  (match-define (grid width height data) g)
  (define current-group (make-parameter 1))
  (for* ([x (in-range width)] [y (in-range height)])
    (define p (point x y))
    (when (trace! g p (current-group) 0)
      (current-group (+ (current-group) 1)))))

; Turn a number into a consistent random color
(define color-for
  (let ([cache (make-hash)])
    (hash-set! cache #f (list 0 0 0))
    (hash-set! cache 0  (list 0 0 0))
    (λ (n)
      (hash-ref! cache n (thunk (list (random 256) (random 256) (random 256)))))))

; Render a grid into a bitmap
(define (render g)
  (match-define (grid width height data) g)
  
  (define images
    (for/list ([y (in-range height)])
      (for/list ([x (in-range width)])
        (define n (grid-ref g (point x y)))
        (match-define (node direction group) n)
        
        (cc-superimpose 
         (colorize (filled-rectangle 15 15) "white")
         (colorize (text (symbol->string direction)) (color-for group))))))
  
  (pict->bitmap (apply vc-append (map (λ (row) (apply hc-append row)) images))))



(define g
  (with-input-from-string
   #;">v
^<"
   #;">>>vv
>^^v^
>^<<^
"
   #;"v<^><>>v><>^<>vvv^^>
>^<>^<<v<>>^v^v><^<<
v^^>>>>>><v^^<^vvv>v
^^><v<^^<^<^^>>>v>v>
^<>vv^><>^<^^<<^^><v
^vv<<<><>>>>^<>^^^v^
^<^^<^>v<v^<>vv<^v<>
v<>^vv<^>vv>v><v^>^^
>v<v><^><<v>^^>>^<>^
^v<>^<>^>^^^vv^v>>^<
v>v^^<>><<<^^><^vvv^"
   "^^v>>v^>>v<<<v>v<>>>>>>>>^vvv^^vvvv<v^^><^^v>
>><<>vv<><<<^><^<^v^^<vv>>^v<v^vv^^v<><^>><v<
vv<^v<v<v<vvv>v<v<vv<^<v<<<<<<<<^<><>^><^v>>>
<v<v^^<v<>v<>v<v<^v^>^<^<<v>^v><^v^>>^^^<><^v
^>>>^v^v^<>>vvv>v^^<^<<<><>v>>^v<^^<>v>>v<v>^
^^^<<^<^>>^v>>>>><>>^v<^^^<^^v^v<^<v^><<^<<<>
v<>v^vv^v<><^>v^vv>^^v^<>v^^^>^>vv<^<<v^<<>^v
<<<<<^<vv<^><>^^>>>^^^^<^<^v^><^v^v>^vvv>^v^^
<<v^<v<<^^v<>v>v^<<<<<>^^v<v^>>>v^><v^v<v^^^<
^^>>^<vv<vv<>v^<^<^^><><^vvvv<<v<^<<^>^>vv^<v
^^v^>>^>^<vv^^<>>^^v>v>>v>>v^vv<vv^>><>>v<<>>
^v<^v<v>^^<>>^>^>^^v>v<<<<<>><><^v<^^v><v>^<<
v>v<><^v<<^^<^>v>^><^><v^><v^^^>><^^<^vv^^^>^
v><>^><vv^v^^>><>^<^v<^><v>^v^<^<>>^<^vv<v>^v
><^<v>>v>^<<^>^<^^>v^^v<>>v><<>v<<^><<>^>^v<v
>vv>^>^v><^^<v^>^>v<^v><>vv>v<^><<<<v^<^vv<>v
<><<^^>>^<>vv><^^<vv<<^v^v^<^^^^vv<<>^<vvv^vv
>v<<v^><v<^^><^v^<<<>^<<vvvv^^^v<<v>vv>^>>^<>
^^^^<^<>^^vvv>v^<<>><^<<v>^<<v>>><>>><<^^>vv>
<^<^<>vvv^v><<<vvv<>>>>^<<<^vvv>^<<<^vv>v^><^"
 read-grid))

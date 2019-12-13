#lang racket

; Single argument operations that take and return an integer
(define unary-ops
  (hash 'not     (λ (a) (if (= a 0) 1 0))
        'pointer (λ (a) (error 'pointer "not implemented"))
        'switch  (λ (a) (error 'pointer "not implemented"))))

; pointer: Pops the top value off the stack and rotates the DP clockwise that many steps (anticlockwise if negative).
; switch: Pops the top value off the stack and toggles the CC that many times (the absolute value of that many times if negative).
  
; Two argument operations that take and return an integer
(define binary-ops 
  (hash 'add      +
        'subtract -
        'multiply *
        'divide   quotient
        'mod      remainder
        'greater  (λ (a b) (if (> a b) 1 0))))

(define (decode-direction-pointer dp)
  (case dp
    [(0)    'right]
    [(1 -3) 'down]
    [(2 -2) 'left]
    [(3 -1) 'up]))

(define (decode-codel-chooser cc)
  (case cc
    [(0)    'left]
    [(1)    'right]))

(struct codel (size hue lightness neighbors))
(struct vm (direction-pointer codel-chooser program stack))

(define (step current-vm)
  (match-define (vm direction-pointer codel-chooser program stack) current-vm)
  (match-define (codel size op hue lightness neighbors) program)
  
  ; Determine how the stack changes based on the current command
  (define new-stack 
    (match op
      ['push 
       (match-define (list* stack) stack)
       (list* size stack)]
      [(or 'pop 'pointer 'switch)
       (match-define (list* a stack) stack)
       stack]
      [(? (curry hash-has-key? unary-ops))
       (match-define (list* a stack) stack)
       (list* ((hash-ref unary-ops op) a) stack)]
      [(? (curry hash-has-key? binary-ops))
       (match-define (list* a b stack) stack)
       (list* ((hash-ref unary-ops op) a b) stack)]
      ['duplicate
       (match-define (list* a stack) stack)
       (list* a a stack)]
      ['roll
       (error 'roll "not implemented")]
      ['in
       (list* (read) stack)]))
  
  ; Update the direction pointer and codel chooser
  (define new-direction-pointer
    (if (eq? op 'pointer)
        (remainder (+ direction-pointer (first stack)) 4)
        direction-pointer))
  
  (define new-codel-chooser
    (if (and (eq? op 'switch) (odd? (first stack)))
        (remainder (+ codel-chooser 1))
        codel-chooser))
  
  ; Update our location in the program based on those new values
  (define new-program
    (hash-ref neighbors 
              (list (decode-direction-pointer new-direction-pointer)
                    (decode-codel-chooser new-codel-chooser))
              #f))
  
  ; Create the next vm state
  (and new-program
       (vm new-direction-pointer
           new-codel-chooser
           new-program
           new-state)))


; Test program
#;(let ([a (read)]
        [b (read)])
    (if (> a b)
        (* a b)
        (- a b)))


(let* ([n1 (codel 1 'in 

 
(struct codel (size op hue lightness neighbors))
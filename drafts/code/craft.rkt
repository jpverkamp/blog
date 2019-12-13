#lang racket

(struct recipe (machine input output) #:transparent)

; ----- ----- ----- ----- ----- 

(define (read-recipe [in (current-input-port)])
  (define (add h item count)
    (hash-set h item (string->number (string-trim (or count "1")))))
  
  (cond
    [(or (eof-object? (peek-char in)) (eq? #\newline (peek-char in))) #f]
    [else
     (for/fold ([r (recipe "Craft" (hash) (hash))])
               ([line (in-lines in)] #:break (equal? "" (string-trim line)))
       (match-define (recipe machine input output) r)
       (match line
         [(pregexp #px"@(.*)" (list _ machine))
          (recipe machine input output)]
         [(pregexp #px"> (\\d+ )?(.*)" (list _ count item))
          (recipe machine input (add output item count))]       
         [(pregexp #px"(\\d+ )?(.*)" (list _ count item))       
          (recipe machine (add input item count) output)]))]))

(define (read-recipe-list [in (current-input-port)])
  (for*/list ([i (in-naturals)]
              [r (in-value (read-recipe in))]
              #:break (not r))
    r))

; ----- ----- ----- ----- ----- 

(define (write-recipe r [out (current-output-port)])
  (match-define (recipe machine input output) r)
  
  (when (not (equal? "Craft" machine))
    (fprintf out "@~a\n" machine))
  
  (define (dump h prefix)
    (for ([item (in-list (sort (hash-keys h) string<?))])
      (define count (hash-ref h item))
      (if (= count 1)
          (fprintf out "~a~a\n" prefix item)
          (fprintf out "~a~a ~a\n" prefix count item))))
  
  (dump output "> ")
  (dump input ""))

(define (write-recipe-list r* [out (current-output-port)])
  (for ([r (in-list r*)])
    (write-recipe r)
    (newline)))

(define (forget-recipe r)
  (set! *current-recipes* (filter (λ (each) (not (eq? r each))) *current-recipes*))
  (save!))

; ----- ----- ----- ----- ----- 

(define *current-recipes*
  (if (file-exists? "craft.cache")
      (call-with-input-file "craft.cache" read-recipe-list)
      (list)))

(define (save!)
  (with-output-to-file "craft.cache" 
    #:exists 'replace
    (λ ()
      (write-recipe-list *current-recipes*))))

(define (find-recipe output)
  (for/first ([r (in-list *current-recipes*)]
              #:when (hash-has-key? (recipe-output r) output))
    r))

(define (remove-recipe! output)
  (set! *current-recipes* (for/list ([r (in-list *current-recipes*)]
                                     #:when (not (hash-has-key? (recipe-output r) output)))
                            r))
  (save!))

(define (request-recipe! target)
  (printf "How do you craft '~a'?\n" target)
  (define new-recipe (read-recipe))
  (match-define (recipe machine input output) new-recipe)
  
  (when (hash-empty? output)
    (set! new-recipe (recipe machine input (hash target 1))))
  
  (when (and (equal? machine "Craft") (hash-empty? input))
    (set! new-recipe (recipe "Raw" input output)))
  
  (set! *current-recipes* (cons new-recipe *current-recipes*))
  (save!))

; ----- ----- ----- ----- ----- 

(define current-mode (make-parameter 'output-simple))

(define (craft #:inventory [inventory (hash)] . args)
  (define target
    (let loop ([args args])
      (match args
        [(list) (hash)]
        [(list-rest (? integer? count) item rest)
         (hash-set (loop rest) item count)]
        [(list-rest item rest)
         (hash-set (loop rest) item 1)])))
  
  (define craftings
    (let loop ([to-craft '()]
               [steps '()]
               [inventory inventory])
      (cond
        ; Have everything we need, done
        [(for/and ([(item count) (in-hash target)])
           (>= (hash-ref inventory item 0) count))
         (reverse steps)]
        [else
         (match to-craft
           ; No intermediaries left, add the first missing item
           [`()
            (for/first ([(item count) (in-hash target)]
                        #:when (< (hash-ref inventory item 0) count))
              (loop `((,item ,count)) steps inventory))]
           ; We've finished this intermediary, move on
           [`((,item 0) . ,rest)
            (loop rest steps inventory)]
           ; We have an intermediaries to craft
           [`((,item ,count) . ,rest)
            (cond
              ; We know how to make the next item
              [(find-recipe item)
               => (λ (r)
                    (match-define (recipe machine input output) r)
                    (cond
                      ; We have all of the items necessary to run the first crafting
                      [(andmap (λ (input-item)
                                 (>= (hash-ref inventory input-item 0)
                                     (hash-ref input input-item)))
                               (hash-keys input))
                       
                       (let* ([inventory ; Remove input items from inventory 
                               (for/fold ([inventory inventory])
                                         ([(input-item input-count) (in-hash input)])
                                 (hash-update inventory input-item (curryr - input-count) 0))]
                              [inventory ; Add output items to inventory
                               (for/fold ([inventory inventory])
                                         ([(output-item output-count) (in-hash output)])
                                 (hash-update inventory output-item (curryr + output-count) 0))])
                         (loop `((,item ,(- count 1)) . ,rest)
                               `((1 ,r) . ,steps)
                               inventory))]
                      
                      ; We need some more inputs, find the first that is missing and add it to the queue
                      [else
                       (for*/first ([(input-item input-count) (in-hash input)]
                                    [needed (in-value (- input-count (hash-ref inventory input-item 0)))]
                                    #:when (> needed 0))
                         (loop `((,input-item ,needed) . ,to-craft)
                               steps
                               inventory))]))]
              ; Don't have a receipe, ask the user
              [else
               (request-recipe! item)
               (loop to-craft steps inventory)])])])))
  
  ; Merge each crafting into the first occurance
  (define merged-craftings
    (let loop ([craftings craftings])
      (match craftings
        [`() `()]
        [`((,count ,r) . ,rest)
         (define-values (matches non-matches) 
           (partition (λ (c+r) (equal? (second c+r) r)) rest))
         `((,(+ count (apply + (map first matches))) ,r) . ,(loop non-matches))])))
  
  ; Sort so all raw materials are first
  (define-values (raw-materials non-raw-craftings)
    (partition (λ (c+r) (equal? (recipe-machine (second c+r)) "Raw")) merged-craftings))
  
  ; Print or return, based on mode
  (cond
    [(member (current-mode) '(output output-simple))
     
     (printf "Raw materials:\n")
     (for ([c+r (in-list raw-materials)])
       (match-define `(,count ,(recipe machine input output)) c+r)
       (for ([(output-item output-count) (in-hash output)])
         (define total-count (* count output-count))
         (printf "  ~a ~a" total-count output-item)
         (when (> total-count 64)
           (printf " (~a stacks plus ~a)" (quotient total-count 64) (remainder total-count 64)))
         (newline)))
     (newline)
     
     (printf "Craftings:\n")
     (for ([c+r (in-list non-raw-craftings)])
       (match-define `(,count ,(recipe machine input output)) c+r)
       
       (printf "  ~ax ~a ~a\n"
               count
               (string-join
                (for/list ([(output-item output-count) (in-hash output)])
                  (~a output-item 
                      (if (= output-count 1)
                          ""
                          (~a " (" output-count " each)"))))
                " / ")
               (if (member machine '("Raw" "Craft")) 
                   ""
                   (~a "(via " machine ")")))
       
       (when (eq? (current-mode) 'output)
         (for ([(input-item input-count) (in-hash input)])
           (printf "  \\ ~a ~a\n" (* count input-count) input-item))
         (newline)))]
    [else 
     (append raw-materials non-raw-craftings)]))

(define (big-reactor rods x [y x] [z x])
  (craft 
   ; Floor
   (* x y) "Reactor Casing"
   ; Ceiling
   (+ x x y y -4) "Reactor Casing"
   (- (* (- x 1) (- y 1)) rods) "Reactor Glass"
   rods "Reactor Control Rod"
   ; Corners
   (* 4 (- z 2)) "Reactor Casing"
   ; Walls
   1 "Reactor Controller"
   2 "Reactor Access Port"
   1 "Reactor Power Tap"
   (- (+ (* 2 (- x 2) (- z 2))
         (* 2 (- y 2) (- z 2)))
      4) "Reactor Glass"))
   
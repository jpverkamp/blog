
(define current-counters (make-hash))

(define (counter key)
  (hash-update! current-counters key add1 0)
  (hash-ref current-counters key))

(define (reset-counters! post site)
  (set! current-counters (make-hash)))

(register-plugin 'counter counter)
(register-post-render-plugin 'reset-counters reset-counters!)

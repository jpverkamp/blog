(define (latex . body*)
  (match body*
    [`(inline . ,body*)
     `(span "\\(" ,(apply ~a body*) "\\)")]
    [`(block . ,body*)
     `(div "$$" ,(apply ~a body*) "$$")]
    [any ; default to block mode
     `(div "$$" ,(apply ~a body*) "$$")]))

(register-plugin 'latex latex)

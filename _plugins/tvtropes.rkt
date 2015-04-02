(define (trope text [title text])
  `(a ((href ,(~a "http://tvtropes.org/pmwiki/pmwiki.php/Main/"
                  (apply ~a
                         (for/list ([word (in-list (string-split text))])
                           (~a (char-upcase (string-ref word 0))
                               (string-downcase (substring word 1))))))))
      ,text))

(register-plugin 'trope trope)
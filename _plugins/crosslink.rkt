(define crosslink
  (case-lambda
    [(text) (crosslink text text)]
    [(target text)
     #;(printf "~a is looking for ~a\n" (post "title") target)
     
     (or
      ; Find the post that we're linking to
      (let ([target (slug target)])
        (for/first ([target-post (in-list (site "posts"))]
                    #:when (equal? target (or (target-post "slug") (slug (target-post "title")))))
          `(a ((href ,(~a (or (site "url") "") "/" (target-post "permalink")))) ,text)))
      
      ; If we cannot, error out
      (error 'crosslink "Cannot find crosslink for ~a in ~a" target (post "title")))]))

(register-plugin 'crosslink crosslink)
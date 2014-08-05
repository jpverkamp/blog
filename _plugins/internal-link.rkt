(define internal-link
  (case-lambda
    [(name)
     (error 'internal-link "not implemented")]
    [(link name)
     (define target-post
       (for/first ([post (in-list (site "posts"))]
                   #:when (equal? (post "permalink") link))
         post))
     
     (when (not target-post)
       (error 'internal-link "link ~a does not exist" link))
     
     (define full-link (regexp-replace* #px"//" (~a (or (site "url") "") "/" link) "/"))
     `(a ((href ,full-link)
          (title ,(target-post "title")))
         ,name)]))

(register-plugin 'internal-link internal-link)
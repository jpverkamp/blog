(define emoji-db
  (for/hash ([file (in-list (directory-list (build-path "_static" "emoji")))])
    (values (~a ":" (regexp-replace #px"\\.\\w+$" (path->string file) "") ":") file)))

(define (emoji str)
  (cond
    [(or (hash-ref emoji-db str #f)
         (hash-ref emoji-db (~a ":" str ":") #f))
     => (λ (path) 
          `(img ((alt ,(string-trim str ":"))
                 (class "emoji") 
                 (src ,(~a "/emoji/" path)))))]
    [else str]))

(register-plugin 'emoji emoji)

(define (emojify post site)
  (when (post "content")
    (post "content" 
          (regexp-replace*  ":[a-z0-9_-]+:" 
                            (post "content")
                            (λ (match)
                              (if (hash-has-key? emoji-db match)
                                  (~a "@emoji{" match "}")
                                  match))))))

(register-pre-render-plugin 'emojify emojify)
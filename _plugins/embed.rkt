(define (embed #:target [target #f] #:lightbox [lightbox #f] #:class [class #f] text)
  (define (absolute-path src)
    (cond
      [(regexp-match #px"://" src) src]
      [else (~a (or (site "url") "/") "/" (or (post "permalink") ".") "/" src)]))
  
  (cond
    [(regexp-match #px"\\.(png|jpg|jpeg|gif)$" text)
     `(a ((data-toggle "lightbox")
          (href ,(absolute-path (or target text)))
          ,@(if class `((class ,class)) `()))
         (img ((src ,(absolute-path text)))))]
    [(regexp-match #px"\\.(mp3|wav|ogg)$" (absolute-path (or target text)))
     => (λ (match)
          `(audio ((controls "controls"))
                  (source ((src ,(absolute-path (or target text)))
                           (type ,(cadr (assoc (cadr match) 
                                               '(("mp3" "audio/mpeg")
                                                 ("ogg" "audio/ogg")
                                                 ("wav" "audio/wav")))))))
                  "Your browser does not support HTML5 audio."))]
    [else
     `(a ((href ,(absolute-path (or target text)))
          ,@(if lightbox `((data-toggle "lightbox")) '())
          ,@(if class `((class ,class)) `()))
         ,text)]))
   
(register-plugin 'embed embed)
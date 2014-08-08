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
    [else
     `(a ((href ,(absolute-path (or target text)))
          ,@(if lightbox `((data-toggle "lightbox")) '())
          ,@(if class `((class ,class)) `()))
         ,text)]))
   
(register-plugin 'embed embed)
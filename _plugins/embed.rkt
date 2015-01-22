(define (embed #:target [target #f]     ; The target for links / embed for lightbox
               #:lightbox [lightbox #f] ; If we should show as an embedded lightbox
               #:class [class #f]       ; Any custom classes to add
               #:width [width #f]       ; Image dimensions
               #:height [height #f]     ;   "          "
               #:title [title #f]       ; title attribute for a, alt for img
               text)                    ; The content of the embed (normally an image)
  
  ; Make sure that paths are absolute to account for archive pages
  (define (absolute-path src)
    (cond
      [(regexp-match #px"://" src) src]
      [else (~a (or (site "url") "/") "/" (or (post "permalink") ".") "/" src)]))
  
  ; Auto lightbox images if target is not set
  (when (and (regexp-match #px"\\.(png|jpg|jpeg|gif)$" text)
             (not lightbox)
             (not target))
    (set! lightbox #t))
  
  (cond
    ; Embedding a youtube video
    [(regexp-match #px"https?://www.youtube.com/watch\\?v=(.*)" text)
     => (λ (match)
          `(iframe ((width 560)
                    (height 315)
                    (src ,(~a "//www.youtube.com/embed/" (cadr match)))
                    (frameborder 0)
                    (allowfullscreen allowfullscreen))))]
    ; Embedding an image
    [(regexp-match #px"\\.(png|jpg|jpeg|gif)$" text)
     `(a ((href ,(absolute-path (or target text)))
          ,@(if lightbox `((data-toggle "lightbox")) '())
          ,@(if class `((class ,class)) `())
          ,@(if title `((title ,title)) `()))
         (img (,@(if width `((width ,width)) `())
               ,@(if height `((height ,height)) `())
               ,@(if title `((alt ,title)) `())
               (src ,(absolute-path text)))))]
    ; Embed static html content
    [(regexp-match #px"\\.(html?)$" text)
     `(iframe (,@(if width `((width ,width)) `())
               ,@(if height `((height ,height)) `())
               (frameBorder "0")
               (scrolling "no")
               (style "overflow: hidden")
               (src ,(absolute-path text))))]
    ; Embedding an audio file
    [(regexp-match #px"\\.(mp3|wav|ogg)$" (absolute-path (or target text)))
     => (λ (match)
          `(audio ((controls "controls"))
                  (source ((src ,(absolute-path (or target text)))
                           (type ,(cadr (assoc (cadr match) 
                                               '(("mp3" "audio/mpeg")
                                                 ("ogg" "audio/ogg")
                                                 ("wav" "audio/wav")))))))
                  "Your browser does not support HTML5 audio."))]
    ; General embeds
    [else
     `(a ((href ,(absolute-path (or target text)))
          ,@(if lightbox `((data-toggle "lightbox")) '())
          ,@(if class `((class ,class)) `())
          ,@(if title `((title ,title)) `()))
         ,text)]))
   
(register-plugin 'embed embed)
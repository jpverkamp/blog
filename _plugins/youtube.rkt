(define (youtube video)
  `(iframe ((width "560")
            (height "315")
            (src ,(~a "//www.youtube.com/embed/" video))
            (frameborder "0")
            (allowfullscreen "allowfullscreen"))))

(register-plugin 'youtube youtube)
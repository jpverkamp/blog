(define (flickr-gallery id)
  `(div (div ((class "flickr-gallery")
              (data-set-id ,(~a id))
              (data-per-page "30")))
        (p (a ((href ,(~a "https://flickr.com/photos/jpverkamp/sets/" id)))
              "View on Flickr"))))

(register-plugin 'flickr-gallery flickr-gallery)

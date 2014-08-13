
(define post-alternates (make-parameter (list)))
(define has-selector (make-parameter #f))

; Inline tag to add alternate versions of content
; One tag will be active at any given time, all alternates with that tag will be visible, all others hidden
(define (alternate tag . lines)
  (when (not (member tag (post-alternates)))
    (post-alternates (cons tag (post-alternates))))
  
  `(div ((data-alternate ,tag))
        "<!--allow-paragraphs-->\n"
        ,@lines))

(register-plugin 'alternate alternate)

; Display an alternate selector here (you cannot change alternates if this is not present)
(define (alternate-selector)
  (has-selector #t) 
  `(div (alternate-selector)))

(register-plugin 'alternate-selector alternate-selector)

; Add the alternate switcher as an inline tag
; This has to be done here, so we know the list that we're going to generate
(define (add-alternate-switcher post site)
  (when (has-selector)
    (post "content" 
          (regexp-replace*
           #px"<alternate-selector></alternate-selector>"
           (post "content")
           (apply ~a `("<div class=\"btn-group\">"
                       ,@(for/list ([alt (in-list (reverse (post-alternates)))])
                           (~a "<button type=\"button\" class=\"btn btn-default btn-xs alt-selector\" data-alternate-target=\""
                               alt
                               "\">"
                               alt
                               "</button>"))
                       "</div>"))))))

(register-post-render-plugin 'add-alternate-switcher add-alternate-switcher)

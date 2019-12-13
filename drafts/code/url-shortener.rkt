#lang web-server

(require json
         racket/runtime-path
         web-server/servlet
         web-server/servlet-env)

(define-runtime-path SHORT_CODE_DB "short-codes.tab")
(define-runtime-path STATS_DB "stats.tab")

(define SHORT_CODE_LENGTH 7)
(define SHORT_CODE_ALPHABET "abcdefghijklmnopqrstuvwxyz0123456789")

(define LIST_PER_PAGE 100)

(define stats (make-hash))

(define (response/json jsexpr)
  (response/full
   200 #"OK" (current-seconds) #"application/json" '()
   (list (string->bytes/utf-8 (jsexpr->string jsexpr)))))

; Either load the previous short code database or generate a new one
(define short-codes (make-hash))
(when (file-exists? SHORT_CODE_DB)
  (with-input-from-file SHORT_CODE_DB
    (λ ()
      (for ([line (in-lines)])
        (match-define (list short-code url created-at) (string-split line "\t"))
        (hash-set! short-codes short-code url)))))

; Generate a new short code, verifying that it is unique
; Store it in the database, writing through to the file system
(define (generate-short-code url)
  (define short-code
    (let loop ()
      (define new-code
        (list->string
         (for/list ([i (in-range SHORT_CODE_LENGTH)])
           (string-ref SHORT_CODE_ALPHABET (random (string-length SHORT_CODE_ALPHABET))))))

      (if (hash-has-key? short-codes new-code)
          (loop)
          new-code)))

  (hash-set! short-codes short-code url)
  (thread
   (λ ()
     (with-output-to-file SHORT_CODE_DB
       #:exists 'append
       (λ () (printf "~a\t~a\t~a\n" short-code url (current-seconds))))))

  short-code)

; Redirect the user to the given shortcode
(define (redirect req short-code)
  (cond
    [(hash-ref short-codes short-code #f)
     => (λ (url)
          (thread
           (λ ()
             (with-output-to-file STATS_DB
               #:exists 'append
               (λ () (printf "~a\t~a\t~a\n" short-code url (current-seconds))))))
          (redirect-to url))]
    [else
     (response/xexpr `(div "invalid short code: " ,short-code))]))

; Generate a new short code
(define (new req)
  (define bindings (request-bindings req))
  (response/xexpr
   (let/ec return
     (when (not (exists-binding? 'url bindings))
       (return "no url specified"))

     (define url (extract-binding/single 'url bindings))

     (when (not (regexp-match #px"^(?i:https?://[a-z0-9]+(\\.[a-z0-9])+)" url))
       (return "invalid url specified"))

     (generate-short-code url))))

(define-values (dispatch get-url)
  (dispatch-rules
   [("new") new]
   [((string-arg)) redirect]))

(serve/servlet
 dispatch
 #:command-line? #t
 #:servlet-regexp #px""
 #:stateless? #t)

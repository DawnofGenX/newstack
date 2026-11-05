#lang racket/base

;; The whole route table as one pure function: (method, path, query, body) in,
;; (status, body string) out. The server only moves bytes.
(provide reply
         reply-status
         reply-body
         route
         json-string
         counts->jsexpr)

(require json
         net/uri-codec
         racket/string
         "counts.rkt")

(struct reply (status body) #:transparent)

(define (error-reply status code [detail #f])
  (reply status (json-string (if detail
                                 (hasheq 'error code 'detail detail)
                                 (hasheq 'error code)))))

(define (stats-reply text)
  (reply 200
         (json-string (hasheq 'text text
                              'lines (counts-lines (count-text text))
                              'words (counts-words (count-text text))
                              'bytes (counts-bytes (count-text text))))))

(define (split-pair pair)
  ;; split at the FIRST "=" only: a value may contain more of them
  (let loop ([index 0])
    (cond
      [(>= index (string-length pair)) (values pair "")]
      [(char=? (string-ref pair index) #\=)
       (values (substring pair 0 index) (substring pair (add1 index)))]
      [else (loop (add1 index))])))

(define (query-param query name)
  (define cleaned (drop-question query))
  (for/or ([pair (in-list (string-split cleaned "&"))])
    (define-values (key raw) (split-pair pair))
    (and (string=? key name) (form-urlencoded-decode raw))))

(define (drop-question query)
  (if (and (> (string-length query) 0) (char=? (string-ref query 0) #\?))
      (substring query 1)
      query))

(define (body-text body)
  ;; 'invalid for anything that is not one JSON object, 'missing for an object
  ;; whose text is absent or not a string, (list 'text value) otherwise.
  (define parsed
    (with-handlers ([exn:fail? (lambda (_e) 'invalid)])
      (string->jsexpr body)))
  (cond
    [(eq? parsed 'invalid) 'invalid]
    [(eq? parsed 'null) 'invalid]
    [(not (hash? parsed)) 'invalid]
    [else
     (define value (hash-ref parsed 'text 'absent))
     (if (string? value) (list 'text value) 'missing)]))

(define (route method path query body)
  (cond
    [(and (string=? method "GET") (string=? path "/health"))
     (reply 200 (json-string (hasheq 'status "ok")))]
    [(and (string=? method "GET") (string=? path "/stats"))
     (define text (query-param query "text"))
     (if text (stats-reply text) (error-reply 422 "missing_text"))]
    [(and (string=? method "POST") (string=? path "/stats"))
     (define parsed (body-text body))
     (cond
       [(eq? parsed 'invalid) (error-reply 422 "invalid_json")]
       [(eq? parsed 'missing) (error-reply 422 "missing_text")]
       [else (stats-reply (cadr parsed))])]
    [(or (string=? path "/health") (string=? path "/stats"))
     (error-reply 405 "method_not_allowed")]
    [else (error-reply 404 "not_found"
                       (format "no route for ~a ~a" method path))]))

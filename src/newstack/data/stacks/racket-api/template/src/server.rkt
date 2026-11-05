#lang racket/base

;; The only place that knows about sockets: read the request, hand
;; (method, path, query, body) to the pure route table, write the reply.
(require web-server/servlet-env
         web-server/http
         net/url
         net/uri-codec
         racket/string
         "contract.rkt")

;; web-server hands us a parsed `url`; re-encode its query pairs so the
;; contract's own decoder stays the single place that decodes anything.
(define (query-string uri)
  (define raw (url-query uri))
  (cond
    [(not raw) ""]
    [(string? raw) raw]
    [else
     (string-join (for/list ([pair (in-list raw)])
                    (format "~a=~a"
                            (car pair)
                            (uri-encode (cdr pair))))
                  "&")]))

(define (request-path uri)
  (car (string-split (url->string uri) "?")))

(define (request-body-string request)
  (define raw (request-post-data/raw request))
  (if raw (bytes->string/utf-8 raw #\?) ""))

(define (handler request)
  (define uri (request-uri request))
  (define outcome
    (route (bytes->string/utf-8 (request-method request))
           (request-path uri)
           (query-string uri)
           (request-body-string request)))
  (response/full (reply-status outcome)
                 #f
                 0
                 #f
                 (list (make-header #"content-type" #"application/json"))
                 (list (string->bytes/utf-8 (reply-body outcome)))))

(define port
  (string->number (or (getenv "PORT") "8080")))

(serve/servlet handler
               #:port port
               #:listen-ip "127.0.0.1"
               #:servlet-regexp #rx""
               #:stateless? #t
               #:launch-browser? #f)

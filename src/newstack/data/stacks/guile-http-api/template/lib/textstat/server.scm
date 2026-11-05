;;; The socket half. Everything here is glue: read the request, ask the route
;;; table, write one JSON document back.
(define-module (textstat server)
  #:use-module (rnrs bytevectors)
  #:use-module (rnrs io ports)
  #:use-module (ice-9 format)
  #:use-module (web request)
  #:use-module (web response)
  #:use-module (web server)
  #:use-module (web uri)
  #:use-module (textstat contract)
  #:export (make-handler start))

(define (request-body-bytes body)
  (cond
   ((port? body)
    (let ((data (get-bytevector-all body)))
      (if (eof-object? data) (make-bytevector 0) data)))
   ((bytevector? body) body)
   ((string? body) (string->utf8 body))
   (else (make-bytevector 0))))

(define (reply->response reply)
  (values (build-response #:code (reply-status reply)
                          #:headers '((content-type . (application/json))))
          (string->utf8 (reply-body reply))))

(define (make-handler)
  (lambda (request body)
    (let* ((uri (request-uri request))
           (method (request-method request))
           (path (uri-path uri))
           (query (uri-query uri))
           (text (utf8->string (request-body-bytes body))))
      (reply->response
       (route (if (symbol? method) (symbol->string method) (if (string? method) method (format #f "~a" method)))
              path
              (or query "")
              text)))))

(define (start)
  (let* ((port (string->number (or (getenv "PORT") "8080")))
         (host (or (getenv "ADDR") "127.0.0.1")))
    (format #t "listening on http://~a:~a~%" host port)
    (format #t "~a" (run-server (make-handler) 'http (list #:port port #:host host)))))

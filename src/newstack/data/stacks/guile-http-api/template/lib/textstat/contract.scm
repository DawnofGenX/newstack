;;; The route table. A method, a path, a query and a body in; a status and a
;;; JSON document out. No socket, no clock, no randomness.
(define-module (textstat contract)
  #:use-module (rnrs bytevectors)
  #:use-module (ice-9 format)
  #:use-module (ice-9 string-fun)
  #:use-module (srfi srfi-1)
  #:use-module (srfi srfi-9)
  #:use-module (web uri)
  #:use-module (textstat counts)
  #:use-module (json)
  #:export (make-reply reply? reply-status reply-body route))

(define-record-type <reply>
  (make-reply status body)
  reply?
  (status reply-status)
  (body reply-body))

(define (error-reply status code detail)
  (make-reply status
              (if detail
                  (string-append "{\"error\":\"" code "\",\"detail\":\"" (json-quote detail) "\"}")
                  (string-append "{\"error\":\"" code "\"}"))))

(define (stats-reply text)
  (make-reply 200 (counts->json text (counts-of-bytevector (string->utf8 text)))))

;;; "?text=hello%20world%0A" -> "hello world\n"; #f when the key is absent.
(define (query-value query name)
  (define (decode raw)
    (uri-decode (string-map (lambda (c) (if (char=? c #\+) #\space c)) raw)))
  (if (or (not query) (string=? query ""))
      #f
      (let loop ((pairs (string-split query #\&)))
        (if (null? pairs)
            #f
            (let* ((pair (car pairs))
                   (equals (string-index pair #\=)))
              (if (and equals (string=? (substring pair 0 equals) name))
                  (decode (substring pair (+ equals 1) (string-length pair)))
                  (loop (cdr pairs))))))))

;;; The body is either a JSON object, something that is not JSON at all, or a
;;; JSON object with no usable "text" member. Only guile-json decides which.
(define (body-text body)
  (catch #t
    (lambda ()
      (let ((parsed (json-string->scm body)))
        (if (and (list? parsed) (assoc "text" parsed))
            (let ((value (assoc-ref parsed "text")))
              (if (string? value) (list 'text value) 'missing))
            'missing)))
    (lambda (key . args) 'invalid)))

(define (route method path query body)
  (cond
   ((and (string=? method "GET") (string=? path "/health"))
    (make-reply 200 "{\"status\":\"ok\"}"))
   ((and (string=? method "GET") (string=? path "/stats"))
    (let ((text (query-value query "text")))
      (if text (stats-reply text) (error-reply 422 "missing_text" #f))))
   ((and (string=? method "POST") (string=? path "/stats"))
    (let ((parsed (body-text body)))
      (cond
       ((eq? parsed 'invalid) (error-reply 422 "invalid_json" #f))
       ((eq? parsed 'missing) (error-reply 422 "missing_text" #f))
       (else (stats-reply (cadr parsed))))))
   ((or (string=? path "/health") (string=? path "/stats"))
    (error-reply 405 "method_not_allowed" #f))
   (else (error-reply 404 "not_found" (format #f "no route for ~a ~a" method path)))))

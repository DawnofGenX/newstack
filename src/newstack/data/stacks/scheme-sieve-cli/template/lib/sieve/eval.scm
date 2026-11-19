;;; Tiny integer expression evaluator: + - * / and parentheses.
(define-module (sieve eval)
  #:export (eval-expr))

(define *src* "")
(define *pos* 0)

(define (set-src! s)
  (set! *src* s)
  (set! *pos* 0))

(define (src-len) (string-length *src*))

(define (skip-ws)
  (when (and (< *pos* (src-len))
             (char-whitespace? (string-ref *src* *pos*)))
    (set! *pos* (+ *pos* 1))
    (skip-ws)))

(define (peek-char)
  (if (>= *pos* (src-len)) #f (string-ref *src* *pos*)))

(define (advance!) (set! *pos* (+ *pos* 1)))

(define (parse-number)
  (skip-ws)
  (let ((start *pos*))
    (when (and (< *pos* (src-len))
               (char=? (string-ref *src* *pos*) #\-))
      (advance!))
    (let loop ()
      (when (and (< *pos* (src-len))
                 (char-numeric? (string-ref *src* *pos*)))
        (advance!)
        (loop)))
    (if (= *pos* start)
        (error "expected number")
        (string->number (substring *src* start *pos*)))))

(define (parse-factor)
  (skip-ws)
  (let ((c (peek-char)))
    (cond
     ((not c) (error "unexpected end"))
     ((char=? c #\() (advance!) (let ((v (parse-expr))) (skip-ws)
                                 (when (or (not (peek-char)) (not (char=? (peek-char) #\))))
                                   (error "missing )"))
                                 (advance!) v))
     (else (parse-number)))))

(define (parse-term)
  (let ((v (parse-factor)))
    (let loop ((v v))
      (skip-ws)
      (let ((c (peek-char)))
        (cond
         ((and c (char=? c #\*)) (advance!) (loop (* v (parse-factor))))
         ((and c (char=? c #\/)) (advance!)
          (let ((d (parse-factor)))
            (if (= d 0) (error "division by zero") (loop (quotient v d)))))
         (else v))))))

(define (parse-expr)
  (let ((v (parse-term)))
    (let loop ((v v))
      (skip-ws)
      (let ((c (peek-char)))
        (cond
         ((and c (char=? c #\+)) (advance!) (loop (+ v (parse-term))))
         ((and c (char=? c #\-)) (advance!) (loop (- v (parse-term))))
         (else v))))))

(define (eval-expr s)
  (set-src! s)
  (let ((v (parse-expr)))
    (skip-ws)
    (if (>= *pos* (src-len))
        v
        (error "trailing input"))))
#lang racket/base

;; Everything between the parsed arguments and the outside world: which rows to
;; print, how wide the columns are, and which exit code to use.  The IO is a
;; hash of thunks, so the tests hand it a fake filesystem.

(require racket/list
         racket/string
         "counts.rkt"
         "options.rkt")

(provide (struct-out io)
         runner-program
         run)

(struct io (read-file read-stdin out err) #:transparent)

(define runner-program "{{ npm_name }}")

(define exit-ok 0)
(define exit-unreadable 1)
(define exit-usage 2)

(define (pad-left text width)
  (string-append (make-string (max 0 (- width (string-length text))) #\space) text))

(define (row-width figures rows)
  (define digits
    (for*/list ([row rows]
                [value (in-list (counts-columns figures (cdr row)))])
      (string-length (number->string value))))
  (apply max (cons 1 digits)))

(define (format-row figures label width c)
  (string-join
   (append (for/list ([value (in-list (counts-columns figures c))])
             (pad-left (number->string value) width))
           (list label))
   " "))

(define (read-row path io)
  (if (equal? path "-")
      (cons path (counts-of-bytes ((io-read-stdin io))))
      (let ([data ((io-read-file io) path)])
        (if data
            (cons path (counts-of-bytes data))
            (begin
              ((io-err io) (string-append "error: cannot open '" path "'\n"))
              #f)))))

(define (run arguments io)
  (define parsed (parse-args arguments))
  (case (options-status parsed)
    [(help)
     ((io-out io) (usage runner-program))
     exit-ok]
    [(version)
     ((io-out io) (string-append runner-program " " tool-version "\n"))
     exit-ok]
    [(error)
     ((io-err io) (string-append runner-program ": " (options-message parsed) "\n"
                                 "Try '" runner-program " --help' for more information.\n"))
     exit-usage]
    [else
     (define figures (options-figures parsed))
     (define files (options-files parsed))
     (define operands (if (null? files) (list "-") files))
     ;; Read everything first: a row is printed only for what could be read, a
     ;; failure sets the exit code, and one bad file does not hide the others.
     (define printable (filter values (map (lambda (path) (read-row path io)) operands)))
     (cond
       [(null? printable) exit-unreadable]
       [else
        (define width (row-width figures printable))
        (define total
          (for/fold ([acc (counts 0 0 0)]) ([row (in-list printable)])
            (counts-add acc (cdr row))))
        (for ([row (in-list printable)])
          ((io-out io) (string-append (format-row figures (car row) width (cdr row)) "\n")))
        (when (> (length operands) 1)
          ((io-out io) (string-append (format-row figures "total" width total) "\n")))
        (if (= (length printable) (length operands)) exit-ok exit-unreadable)])]))

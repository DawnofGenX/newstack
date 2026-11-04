;;; Everything the CLI decides, with the four side effects injected: reading a
;;; file, reading standard input, writing a line out, writing a line to stderr.
(define-module (textstat runner)
  #:use-module (srfi srfi-9)
  #:use-module (srfi srfi-13)
  #:use-module (textstat counts)
  #:use-module (textstat options)
  #:export (make-io io? io-read-file io-read-stdin io-out io-err
            run program-name))

(define-record-type <io>
  (make-io read-file read-stdin out err)
  io?
  (read-file io-read-file)
  (read-stdin io-read-stdin)
  (out io-out)
  (err io-err))

(define program-name "{{ npm_name }}")

(define (digits value)
  (string-length (number->string value)))

(define (pad-left width value)
  (let* ((text (number->string value))
         (fill (- width (string-length text))))
    (if (> fill 0)
        (string-append (make-string fill #\space) text)
        text)))

(define (any-list pred items)
  (cond ((null? items) #f)
        ((pred (car items)) #t)
        (else (any-list pred (cdr items)))))

(define (cells figures tally width)
  (let loop ((rest (counts-columns figures tally)) (acc '()))
    (if (null? rest)
        (reverse acc)
        (loop (cdr rest) (cons (pad-left width (car rest)) acc)))))

(define (row-text figures tally width)
  (string-append (string-join (cells figures tally width) " ")))

;;; wc's padding, copied rather than guessed: one figure from one readable
;;; operand is not padded at all; anything read from a pipe gets the widest
;;; cell wc ever needs; otherwise the width is the digit count of the total
;;; byte count of what was read.
(define (row-width figures rows pipe? total-bytes)
  (cond
   ((and (= (length figures) 1) (<= (length rows) 1))
    (if (null? rows)
        1
        (let ((value (car (counts-columns figures (cdr (car rows))))))
          (max 1 (digits value)))))
   (pipe? 7)
   (else (max 1 (digits total-bytes)))))

(define (read-operand path io)
  ;; (values bytevector-or-#f)
  (if (string=? path "-")
      (call-with-current-continuation
       (lambda (return)
         (catch #t
                (lambda () (return ((io-read-stdin io))))
                (lambda (key . args) (return #f)))))
      (call-with-current-continuation
       (lambda (return)
         (catch #t
                (lambda () (return ((io-read-file io) path)))
                (lambda (key . args) (return #f)))))))

(define (run args io)
  (let* ((parsed (parse-args args))
         (status (parsed-status parsed)))
    (cond
     ((eq? status 'help)
      ((io-out io) (usage program-name))
      0)
     ((eq? status 'version)
      ((io-out io) (string-append tool-version "\n"))
      0)
     ((eq? status 'usage-error)
      ((io-err io) (string-append program-name ": " (parsed-message parsed) "\n"))
      ((io-err io) (string-append "Try '" program-name " --help' for more information.\n"))
      2)
     (else
      (let* ((figures (parsed-figures parsed))
             (operands (parsed-files parsed))
             (implicit? (null? operands))
             (operands (if implicit? (list "-") operands))
             (pipe? (any-list (lambda (path) (string=? path "-")) operands)))
        (let loop ((rest operands)
                   (rows '())
                   (total (make-counts 0 0 0))
                   (failed? #f))
          (if (null? rest)
              (let* ((rows (reverse rows))
                     (width (row-width figures rows pipe? (counts-bytes total))))
                (for-each (lambda (row)
                            ((io-out io)
                             (if (and implicit? (null? (cdr rows)))
                                 (string-append (row-text figures (cdr row) width) "\n")
                                 (string-append (row-text figures (cdr row) width)
                                                " " (car row) "\n"))))
                          rows)
                (if (> (length operands) 1)
                    ((io-out io) (string-append (row-text figures total width) " total\n")))
                (if failed? 1 0))
              (let* ((path (car rest))
                     (data (read-operand path io)))
                (if data
                    (let ((tally (counts-of-bytevector data)))
                      (loop (cdr rest)
                            (cons (cons (if implicit? "" path) tally) rows)
                            (counts-add total tally)
                            failed?))
                    (begin
                      ((io-err io) (string-append "error: cannot open '" path "'\n"))
                      (loop (cdr rest) rows total #t)))))))))))

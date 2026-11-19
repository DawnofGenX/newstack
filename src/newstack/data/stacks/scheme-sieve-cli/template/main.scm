;;; The only file that touches the real process.
(use-modules (sieve runner))

(define (read-file path)
  (let ((port (open-file path "r")))
    (let ((data (get-string-all port)))
      (close-port port)
      data)))

(define (read-stdin)
  (get-string-all (current-input-port)))

(define (write-line text)
  (display text)
  (newline)
  (force-output))

(define (write-error text)
  (display text (current-error-port))
  (force-output (current-error-port)))

(exit (run (cdr (command-line))
           (list read-file read-stdin write-line write-error)))
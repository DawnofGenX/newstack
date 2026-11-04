;;; The only file that touches the real process: three ports and an exit code.
(use-modules (rnrs io ports)
             (textstat counts)
             (textstat options)
             (textstat runner))

(define (read-bytes path)
  (let ((port (open-file path "rb")))
    (let ((data (get-bytevector-all port)))
      (close-port port)
      (if (eof-object? data) #vu8() data))))

(define (read-standard-input)
  (let ((port (open-file "/dev/stdin" "rb")))
    (let ((data (get-bytevector-all port)))
      (close-port port)
      (if (eof-object? data) #vu8() data))))

(define (write-line text)
  (display text)
  (force-output))

(define (write-error text)
  (display text (current-error-port))
  (force-output (current-error-port)))

(exit (run (cdr (command-line))
           (make-io read-bytes read-standard-input write-line write-error)))

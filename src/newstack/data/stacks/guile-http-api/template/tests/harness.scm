;;; A tally and a report. No framework: assertions, a count, an exit code.
(define-module (harness)
  #:use-module (ice-9 format)
  #:export (reset! check check-equal check-text report))

(define passed 0)
(define failed 0)

(define (reset!)
  (set! passed 0)
  (set! failed 0))

(define (check name ok detail)
  (if ok
      (set! passed (+ passed 1))
      (begin
        (set! failed (+ failed 1))
        (format (current-error-port) "FAIL ~a~a~%" name
                (if (string=? detail "") "" (string-append " (" detail ")"))))))

(define (check-equal name actual expected)
  (check name (equal? actual expected)
         (format #f "got ~s, want ~s" actual expected)))

(define (check-text name actual expected)
  (check name (string=? actual expected)
         (format #f "got ~s, want ~s" actual expected)))

(define (report)
  (format #t "checks: ~a, passed: ~a, failed: ~a~%" (+ passed failed) passed failed)
  (if (= failed 0) 0 1))

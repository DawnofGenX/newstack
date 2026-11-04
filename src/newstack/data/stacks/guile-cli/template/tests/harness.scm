;;; A tally and two buffers. No framework: assertions and a report.
(define-module (harness)
  #:use-module (ice-9 format)
  #:export (reset! clear! check check-equal check-text out-text err-text
            collect-out collect-err report))

(define passed 0)
(define failed 0)
(define out-buffer '())
(define err-buffer '())

(define (reset!)
  (set! passed 0)
  (set! failed 0)
  (set! out-buffer '())
  (set! err-buffer '()))

(define (clear!)
  (set! out-buffer '())
  (set! err-buffer '()))

(define (collect-out text) (set! out-buffer (cons text out-buffer)) #t)
(define (collect-err text) (set! err-buffer (cons text err-buffer)) #t)

(define (out-text) (apply string-append (reverse out-buffer)))
(define (err-text) (apply string-append (reverse err-buffer)))

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

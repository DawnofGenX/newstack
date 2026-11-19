(use-modules (sieve primes) (sieve eval))

(define failed 0)
(define (check name ok)
  (if ok (display (string-append "ok: " name "\n"))
      (begin (display (string-append "FAIL: " name "\n")) (set! failed (+ failed 1)))))

(check "primes up to 10" (equal? (primes-up-to 10) '(2 3 5 7)))
(check "primes up to 1" (equal? (primes-up-to 1) '()))
(check "factor 12" (equal? (factorize 12) '(2 2 3)))
(check "factor 7" (equal? (factorize 7) '(7)))
(check "eval basic" (= (eval-expr "2 + 3 * 4") 14))
(check "eval parens" (= (eval-expr "(2 + 3) * 4") 20))

(if (> failed 0) (exit 1) (exit 0))
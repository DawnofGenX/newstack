#lang racket/base

(require rackunit
         "../textstat/counts.rkt")

(define (c text) (counts-of-bytes (string->bytes/utf-8 text)))

(check-equal? (c "alpha beta\ngamma\n") (counts 2 3 17) "plain text")
(check-equal? (c "alpha beta\ngamma") (counts 1 3 16) "no trailing newline")
(check-equal? (c "") (counts 0 0 0) "empty input")
(check-equal? (c "h\u00e9llo w\u00f6rld\n") (counts 1 2 14) "utf-8 counts bytes")
(check-equal? (c "a\tb\nc\vd\re\n") (counts 2 5 10) "tab, vertical tab and form feed separate words")
(check-equal? (c "one\ntwo\n\nthree\n") (counts 4 3 15) "blank lines count")

(check-equal? (counts-add (counts 1 2 3) (counts 10 20 30)) (counts 11 22 33) "totals add")
(check-equal? (counts-columns '(lines words bytes) (counts 1 2 3)) '(1 2 3) "all figures")
(check-equal? (counts-columns '(words) (counts 1 2 3)) '(2) "one figure")
(check-equal? (counts-columns '(bytes lines) (counts 1 2 3)) '(1 3) "columns follow wc's order, not the flags'")

(define data (make-bytes 300 32))
(bytes-set! data 0 10)
(bytes-set! data 150 10)
(check-equal? (counts-of-bytes data) (counts 2 0 300) "whitespace-only input still counts bytes")

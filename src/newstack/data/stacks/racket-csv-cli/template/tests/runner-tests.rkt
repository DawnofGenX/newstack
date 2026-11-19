#lang racket/base

(require rackunit
         racket/string
         "../textstat/runner.rkt")

;; The filesystem the runner sees, as a hash from path to bytes.
(define files
  (hash "a.txt" (string->bytes/utf-8 "alpha beta\ngamma\n")
        "b.txt" (string->bytes/utf-8 "one\n")))

(define (capture args [stdin-bytes #""])
  (define out (open-output-string))
  (define err (open-output-string))
  (define code
    (run args
         (io (lambda (path) (hash-ref files path #f))
             (lambda () stdin-bytes)
             (lambda (text) (display text out))
             (lambda (text) (display text err)))))
  (values code (get-output-string out) (get-output-string err)))

(check-equal? (call-with-values (lambda () (capture '("a.txt"))) list)
              (list 0 " 2  3 17 a.txt\n" "")
              "counts a file")

(check-equal? (call-with-values (lambda () (capture '("-w" "a.txt"))) list)
              (list 0 "3 a.txt\n" "")
              "one figure has no padding")

(check-equal? (call-with-values (lambda () (capture '("a.txt" "b.txt"))) list)
              (list 0 " 2  3 17 a.txt\n 1  1  4 b.txt\n 3  4 21 total\n" "")
              "two files add a total row")

(let-values ([(code out err) (capture '() (string->bytes/utf-8 "alpha beta\ngamma\n"))])
  (check-equal? code 0 "stdin is counted when no file is named")
  (check-equal? out " 2  3 17 -\n" "stdin is labelled -")
  (check-equal? err ""))

(let-values ([(code out err) (capture '("-w") (string->bytes/utf-8 "alpha beta\ngamma\n"))])
  (check-equal? code 0 "stdin with a figure flag")
  (check-equal? out "3 -\n"))

(let-values ([(code out err) (capture '("a.txt" "missing.txt"))])
  (check-equal? code 1 "an unreadable operand sets the exit code")
  (check-equal? out " 2  3 17 a.txt\n 2  3 17 total\n" "what could be read is still printed")
  (check-equal? err "error: cannot open 'missing.txt'\n"))

(let-values ([(code out err) (capture '("--help"))])
  (check-equal? code 0 "help exits 0")
  (check-true (string-contains? out "usage: {{ npm_name }}"))
  (check-equal? err ""))

(let-values ([(code out err) (capture '("--version"))])
  (check-equal? code 0 "version exits 0")
  (check-equal? out "{{ npm_name }} 0.1.0\n"))

(let-values ([(code out err) (capture '("--bogus"))])
  (check-equal? code 2 "a usage error exits 2")
  (check-equal? out "")
  (check-equal? err "{{ npm_name }}: unknown option: --bogus\nTry '{{ npm_name }} --help' for more information.\n"))

(let-values ([(code out err) (capture '("missing.txt"))])
  (check-equal? code 1 "nothing readable is still exit 1")
  (check-equal? out ""))

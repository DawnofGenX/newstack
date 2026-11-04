#lang racket/base

(require rackunit
         "../textstat/options.rkt")

(define (status args) (options-status (parse-args args)))
(define (figures args) (options-figures (parse-args args)))
(define (files args) (options-files (parse-args args)))
(define (message args) (options-message (parse-args args)))

(check-equal? (status '()) 'ok "no arguments is not an error")
(check-equal? (figures '()) '(lines words bytes) "no flags means all three")
(check-equal? (figures '("-l")) '(lines) "one flag")
(check-equal? (figures '("-c" "-l")) '(bytes lines) "flags keep their order")
(check-equal? (figures '("-l" "-l")) '(lines) "duplicates collapse")
(check-equal? (figures '("-lw")) '(lines words) "clustered short flags")
(check-equal? (figures '("--bytes")) '(bytes) "long flag")
(check-equal? (figures '("--" "-l")) '(lines words bytes) "a figure flag after -- is a file")

(check-equal? (files '("a.txt" "b.txt")) '("a.txt" "b.txt") "plain operands")
(check-equal? (files '("-l" "a.txt")) '("a.txt") "flags are not files")
(check-equal? (files '("--" "-l")) '("-l") "the terminator makes the rest files")
(check-equal? (files '("-")) '("-") "a lone dash is a file, meaning stdin")

(check-equal? (status '("--help")) 'help "help")
(check-equal? (status '("-h")) 'help "-h")
(check-equal? (status '("--version")) 'version "version")
(check-equal? (status '("-V")) 'version "-V")
(check-equal? (status '("-w" "--help")) 'help "help wins over counting")

(check-equal? (status '("--bogus")) 'error "unknown long option")
(check-equal? (message '("--bogus")) "unknown option: --bogus" "the message names it")
(check-equal? (status '("-x")) 'error "unknown short option")
(check-equal? (message '("-x")) "unknown option: -x" "clusters report the bad letter")

(check-equal? tool-version "0.1.0" "version string")

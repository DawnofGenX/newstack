;;; The runner is exercised through an injected io record, so no test here
;;; touches the real terminal.
(define-module (runner-tests)
  #:use-module (rnrs bytevectors)
  #:use-module (harness)
  #:use-module (textstat counts)
  #:use-module (textstat options)
  #:use-module (textstat runner)
  #:export (run-suite))

(define plain (string->utf8 "alpha beta\ngamma delta\n"))
(define shorter (string->utf8 "alpha beta\ngamma"))

(define (fake-io files stdin)
  (make-io (lambda (path)
             (let ((hit (assoc path files)))
               (if hit (cdr hit) (error "no such file" path))))
           (lambda () stdin)
           collect-out
           collect-err))

(define (run-case name args files stdin expected-out expected-err expected-code)
  (clear!)
  (let ((code (run args (fake-io files stdin))))
    (check-equal (string-append name ": exit code") code expected-code)
    (check-text (string-append name ": stdout") (out-text) expected-out)
    (check-text (string-append name ": stderr") (err-text) expected-err)))

(define (run-suite)
  (run-case "one file, three figures" '("p1.txt")
            (list (cons "p1.txt" plain)) plain
            " 2  4 23 p1.txt\n" "" 0)
  (run-case "one file, one figure is not padded" '("-l" "p1.txt")
            (list (cons "p1.txt" plain)) plain
            "2 p1.txt\n" "" 0)
  (run-case "two figures share one width" '("-l" "-w" "p1.txt")
            (list (cons "p1.txt" plain)) plain
            " 2  4 p1.txt\n" "" 0)
  (run-case "two files get a total row" '("p1.txt" "p2.txt")
            (list (cons "p1.txt" plain) (cons "p2.txt" shorter)) plain
            " 2  4 23 p1.txt\n 1  3 16 p2.txt\n 3  7 39 total\n" "" 0)
  (run-case "an unreadable file is reported once and the total survives"
            '("p1.txt" "gone.txt")
            (list (cons "p1.txt" plain)) plain
            " 2  4 23 p1.txt\n 2  4 23 total\n"
            "error: cannot open 'gone.txt'\n" 1)
  (run-case "no operand reads standard input without a label" '()
            '() plain
            "      2       4      23\n" "" 0)
  (run-case "an explicit dash is labelled" '("-w" "-")
            '() plain
            "4 -\n" "" 0)
  (run-case "a pipe widens every cell" '("-l" "-w")
            '() plain
            "      2       4\n" "" 0)
  (run-case "help goes to stdout" '("--help") '() plain
            (usage program-name) "" 0)
  (run-case "version goes to stdout" '("--version") '() plain
            "0.1.0\n" "" 0)
  (run-case "an unknown option is refused"
            '("--bogus") '() plain
            ""
            (string-append program-name ": unknown option: --bogus\n"
                           "Try '" program-name " --help' for more information.\n")
            2)
  (run-case "an empty file counts nothing" '("empty.txt")
            (list (cons "empty.txt" #vu8())) plain
            "0 0 0 empty.txt\n" "" 0))

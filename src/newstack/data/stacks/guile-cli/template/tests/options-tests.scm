(define-module (options-tests)
  #:use-module (srfi srfi-13)
  #:use-module (harness)
  #:use-module (textstat options)
  #:export (run-suite))

(define (run-suite)
  (check-equal "no arguments defaults to every figure"
               (parsed-figures (parse-args '())) '(lines words bytes))
  (check-equal "no arguments collects no files"
               (parsed-files (parse-args '())) '())
  (check-equal "short flag"
               (parsed-figures (parse-args '("-l"))) '(lines))
  (check-equal "clustered short flags keep wc order"
               (parsed-figures (parse-args '("-cl"))) '(lines bytes))
  (check-equal "repeated short flags collapse"
               (parsed-figures (parse-args '("-l" "-l"))) '(lines))
  (check-equal "long flag"
               (parsed-figures (parse-args '("--words"))) '(words))
  (check-equal "files are collected in order"
               (parsed-files (parse-args '("a.txt" "b.txt"))) '("a.txt" "b.txt"))
  (check-equal "a lone dash is a file"
               (parsed-files (parse-args '("-"))) '("-"))
  (check-equal "dash after a flag is still a file"
               (parsed-files (parse-args '("-w" "-"))) '("-"))
  (check-equal "double dash ends the flags"
               (parsed-files (parse-args '("--" "-l"))) '("-l"))
  (check-equal "double dash with no flags keeps the defaults"
               (parsed-figures (parse-args '("--" "-l"))) '(lines words bytes))
  (check-equal "help status" (parsed-status (parse-args '("--help"))) 'help)
  (check-equal "short help status" (parsed-status (parse-args '("-h"))) 'help)
  (check-equal "version status" (parsed-status (parse-args '("-V"))) 'version)
  (check-equal "long version status" (parsed-status (parse-args '("--version"))) 'version)
  (let ((bad (parse-args '("--bogus"))))
    (check-equal "unknown long option is refused" (parsed-status bad) 'usage-error)
    (check-text "unknown long option names itself"
                (parsed-message bad) "unknown option: --bogus"))
  (let ((bad (parse-args '("-x"))))
    (check-equal "unknown short option is refused" (parsed-status bad) 'usage-error)
    (check-text "unknown short option names itself"
                (parsed-message bad) "unknown option: -x"))
  (let ((bad (parse-args '("-lx"))))
    (check-equal "unknown letter in a cluster is refused"
                 (parsed-status bad) 'usage-error))
  (check-equal "version string" tool-version "0.1.0")
  (let ((text (usage "prog")))
    (check "usage names the program" (string-contains text "Usage: prog [OPTION]... [FILE]...") #t)
    (check "usage explains standard input"
           (not (eq? (string-contains text "read standard input") #f)) #t)))

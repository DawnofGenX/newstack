;;;; The argv contract.
(in-package :textstat.harness)

(defun parsed (args) (textstat.options:parse-args args))

(defun options-tests ()
  (let ((result (parsed '())))
    (check-equal "no arguments means all three figures"
                 (textstat.options:parsed-figures result) '(:lines :words :bytes))
    (check-equal "no arguments means no files" (textstat.options:parsed-files result) '())
    (check-equal "no arguments is ok" (textstat.options:parsed-status result) :ok))
  (check-equal "-l selects lines" (textstat.options:parsed-figures (parsed '("-l"))) '(:lines))
  (check-equal "--words selects words" (textstat.options:parsed-figures (parsed '("--words"))) '(:words))
  (check-equal "--bytes selects bytes" (textstat.options:parsed-figures (parsed '("--bytes"))) '(:bytes))
  (check-equal "a cluster is additive"
               (textstat.options:parsed-figures (parsed '("-lw"))) '(:lines :words))
  (check-equal "flags keep wc's order whatever order they arrive in"
               (textstat.options:parsed-figures (parsed '("-c" "-l"))) '(:lines :bytes))
  (check-equal "a repeated flag is printed once"
               (textstat.options:parsed-figures (parsed '("-l" "-l"))) '(:lines))
  (check-equal "file operands are collected in order"
               (textstat.options:parsed-files (parsed '("a.txt" "b.txt"))) '("a.txt" "b.txt"))
  (check-equal "flags may follow files"
               (textstat.options:parsed-figures (parsed '("a.txt" "-c"))) '(:bytes))
  (check-equal "a lone dash is a file"
               (textstat.options:parsed-files (parsed '("-"))) '("-"))
  (check-equal "-- ends option parsing"
               (textstat.options:parsed-files (parsed '("--" "-w"))) '("-w"))
  (check-equal "after -- a flag is not a flag"
               (textstat.options:parsed-figures (parsed '("--" "-w"))) '(:lines :words :bytes))
  (check-equal "after -- a word that looks like a figure is a file"
               (textstat.options:parsed-files (parsed '("--" "--lines"))) '("--lines"))
  (let ((result (parsed '("--help"))))
    (check-equal "--help is a status" (textstat.options:parsed-status result) :help))
  (check-equal "-h is help" (textstat.options:parsed-status (parsed '("-h"))) :help)
  (let ((result (parsed '("-V"))))
    (check-equal "-V is a version request" (textstat.options:parsed-status result) :version))
  (check-equal "--version is a version request"
               (textstat.options:parsed-status (parsed '("--version"))) :version)
  (let ((result (parsed '("--bogus"))))
    (check-equal "an unknown long option is a usage error"
                 (textstat.options:parsed-status result) :usage-error)
    (check-equal "the unknown long option is named"
                 (textstat.options:parsed-message result) "unknown option: --bogus"))
  (let ((result (parsed '("-q"))))
    (check-equal "an unknown short option is a usage error"
                 (textstat.options:parsed-status result) :usage-error)
    (check-equal "the unknown short option is named"
                 (textstat.options:parsed-message result) "unknown option: -q"))
  (let ((result (parsed '("-lq"))))
    (check-equal "an unknown letter in a cluster is reported"
                 (textstat.options:parsed-message result) "unknown option: -q"))
  (check-equal "the version is a plain number"
               (textstat.options:tool-version) "0.1.0")
  (check "the usage names the program"
         (search "Usage: textstat" (textstat.options:usage "textstat"))))

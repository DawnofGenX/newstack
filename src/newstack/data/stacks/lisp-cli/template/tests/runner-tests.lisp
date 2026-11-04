;;;; The whole program, with the process replaced by the harness.
(in-package :textstat.harness)

(defun run-with (args &key stdin file-bytes files)
  "Run the program against a fake process. FILE-BYTES is the single readable
fixture; FILES maps a path to bytes for multi-file runs; others fail."
  (let ((out (make-string-output-stream))
        (err (make-string-output-stream)))
    (let ((io (textstat.runner:make-io
               :read-file (lambda (path)
                            (or (cdr (assoc path files :test #'string=)) file-bytes
                                (error "no such file: ~a" path)))
               :read-stdin (lambda () (or stdin
                                          (make-array 0 :element-type '(unsigned-byte 8))))
               :out (lambda (text) (write-string text out))
               :err (lambda (text) (write-string text err)))))
      (let ((code (textstat.runner:run args io)))
        (list code (get-output-stream-string out) (get-output-stream-string err))))))

(defun bytes (&rest values) (make-array (length values) :element-type '(unsigned-byte 8)
                                                     :initial-contents values))

(defun runner-tests ()
  (let ((row (run-with '("a.txt") :file-bytes (bytes 97 32 98 10))))
    (check-equal "a single file prints one row" (second row) (format nil "1 2 4 a.txt~%"))
    (check-equal "a single file exits zero" (first row) 0)
    (check-equal "a single file prints nothing on stderr" (third row) ""))
  (let ((row (run-with '("-w" "a.txt") :file-bytes (bytes 97 32 98 10))))
    (check-equal "one figure prints one column" (second row) (format nil "2 a.txt~%")))
  (let ((row (run-with '("a.txt") :file-bytes (bytes 10 10 10))))
    (check-equal "the width grows with the numbers" (second row) (format nil "3 0 3 a.txt~%")))
  (let ((row (run-with '("a.txt") :file-bytes (bytes))))
    (check-equal "an empty file is three zeroes" (second row) (format nil "0 0 0 a.txt~%"))
    (check-equal "an empty file exits zero" (first row) 0))
  (let ((row (run-with '() :stdin (bytes 97 32 98 10))))
    (check-equal "no operand reads stdin and labels it" (second row) (format nil "1 2 4 -~%"))
    (check-equal "reading stdin exits zero" (first row) 0))
  (let ((row (run-with '("-w") :stdin (bytes 97 32 98 10 99))))
    (check-equal "an explicit figure with stdin" (second row) (format nil "3 -~%")))
  (let ((row (run-with '("-") :stdin (bytes 97 10))))
    (check-equal "an explicit dash reads stdin" (second row) (format nil "1 1 2 -~%")))
  (let* ((a (bytes 97 32 98 10))
         (b (bytes 99 10))
         (row (run-with '("a.txt" "b.txt") :files (list (cons "a.txt" a) (cons "b.txt" b)))))
    (check-equal "two files get a total row"
                 (second row) (format nil "1 2 4 a.txt~%1 1 2 b.txt~%2 3 6 total~%"))
    (check-equal "two files exit zero" (first row) 0))
  (let* ((a (bytes 97 32 98 10))
         (b (bytes 99 10))
         (row (run-with '("-l" "a.txt" "b.txt") :files (list (cons "a.txt" a) (cons "b.txt" b)))))
    (check-equal "the total follows the selected figures"
                 (second row) (format nil "1 a.txt~%1 b.txt~%2 total~%")))
  (let ((row (run-with '("-l" "a.txt"))))
    (check-equal "an unreadable file exits one" (first row) 1)
    (check-equal "an unreadable file prints no row" (second row) "")
    (check "the error names the file" (search "a.txt" (third row))))
  (let ((row (run-with '() :stdin (bytes 97 10))))
    (check-equal "help goes to stdout"
                 (subseq (second (run-with '("--help") :stdin (bytes))) 0 6) "Usage:")
    (check-equal "help exits zero" (first (run-with '("--help") :stdin (bytes))) 0))
  (let ((row (run-with '("--version"))))
    (check-equal "the version is printed" (second row) (format nil "0.1.0~%"))
    (check-equal "the version exits zero" (first row) 0))
  (let ((row (run-with '("--bogus"))))
    (check-equal "a usage error exits two" (first row) 2)
    (check-equal "nothing reaches stdout" (second row) "")
    (check-equal "the complaint names the option"
                 (third row)
                 (format nil "~a: unknown option: --bogus~%Try '~a --help' for more information.~%"
                         (textstat.runner:program) (textstat.runner:program)))))

;;;; JSON reader/writer with sorted-key pretty printing.
(in-package :cl-user)

(load (merge-pathnames "lib/json.lisp"
                       (make-pathname :name nil :type nil
                                     :defaults *load-truename*)))

(defun usage (&optional (code 2))
  (format *error-output* "usage: {{ npm_name }} [FILE]~%")
  (sb-ext:exit :code code))

(defun help ()
  (format *standard-output* "usage: {{ npm_name }} [FILE]~%")
  (sb-ext:exit :code 0))

(defun main ()
  (let ((args (cdr sb-ext:*posix-argv*)))
    (cond
      ((or (equal args '("--help")) (equal args '("-h"))) (help))
      ((> (length args) 1) (usage))
      (t
       (let ((text (if (null args)
                       (with-output-to-string (s)
                         (loop for line = (read-line *standard-input* nil nil)
                               while line do (write-line line s)))
                       (with-open-file (in (car args) :direction :input)
                         (let ((buf (make-string-output-stream)))
                           (loop for line = (read-line in nil nil)
                                 while line do (write-line line buf))
                           (get-output-stream-string buf))))))
         (handler-case
             (let* ((value (json:parse text))
                    (out (json:pretty value)))
               (write-string out *standard-output*)
               (terpri *standard-output*))
           (error (e)
             (format *error-output* "error: ~a~%" e)
             (sb-ext:exit :code 1))))))))

(main)

;;;; argv parsing. No dependencies, no getopt: the contract is small.
(defpackage :textstat.options
  (:use :cl)
  (:export #:parsed #:make-parsed #:parsed-status #:parsed-figures #:parsed-files
           #:parsed-message #:tool-version #:usage #:parse-args))

(in-package :textstat.options)

(defparameter *tool-version* "0.1.0")

(defstruct (parsed (:constructor make-parsed (&key status figures files message)))
  (status :ok :type symbol)        ; :ok :help :version :usage-error
  (figures '(:lines :words :bytes) :type list)
  (files '() :type list)
  (message nil))

(defun tool-version () *tool-version*)

(defun usage (program)
  (format nil "Usage: ~a [OPTION]... [FILE]...~%~
Count lines, words and bytes. With no FILE, or when FILE is -, read standard input.~%~
  -l, --lines     print the newline count~%~
  -w, --words     print the word count~%~
  -c, --bytes     print the byte count~%~
  -h, --help      print this help~%~
  -V, --version   print the version~%"
          program))

(defun figure-for-letter (letter)
  (case letter
    (#\l :lines)
    (#\w :words)
    (#\c :bytes)
    (t nil)))

(defun parse-args (argv)
  "Parse ARGV (a list of strings) into a PARSED. -l/-w/-c are additive and
idempotent; -- makes everything after it a file; a lone - is standard input."
  (let ((figures '())
        (files '())
        (status :ok)
        (message nil)
        (literal nil))
    (flet ((remember (figure)
             (pushnew figure figures :test #'eq))
           (fail (text)
             (setf status :usage-error message text)))
      (dolist (arg argv)
        (cond
          (literal (push arg files))
          ((string= arg "--") (setf literal t))
          ((string= arg "--lines") (remember :lines))
          ((string= arg "--words") (remember :words))
          ((string= arg "--bytes") (remember :bytes))
          ((or (string= arg "--help") (string= arg "-h"))
           (unless (eq status :usage-error) (setf status :help)))
          ((or (string= arg "--version") (string= arg "-V"))
           (unless (eq status :usage-error) (setf status :version)))
          ((and (>= (length arg) 2) (char= (char arg 0) #\-) (char/= (char arg 1) #\-))
           (loop for i from 1 below (length arg)
                 do (let ((figure (figure-for-letter (char arg i))))
                      (if figure
                          (remember figure)
                          (when (eq status :ok)
                            (fail (format nil "unknown option: -~c" (char arg i))))))))
          ((and (> (length arg) 2) (char= (char arg 0) #\-) (char= (char arg 1) #\-))
           (when (eq status :ok)
             (fail (format nil "unknown option: ~a" arg))))
          (t (push arg files)))))
    (make-parsed :status status
                 ;; wc prints its figures in a fixed order however they were asked for.
                 :figures (or (remove-if-not (lambda (figure) (member figure figures))
                                             '(:lines :words :bytes))
                              '(:lines :words :bytes))
                 :files (nreverse files)
                 :message message)))

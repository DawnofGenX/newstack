;;;; A test harness small enough to read: no framework, no dependency.
(defpackage :textstat.harness
  (:use :cl)
  (:export #:reset #:check #:check-equal #:check-text #:report
           #:captured-out #:captured-err #:null-io #:fixture-bytes #:fixture-path))

(in-package :textstat.harness)

(defvar *passed* 0)
(defvar *failed* 0)
(defvar *out* (make-string-output-stream))
(defvar *err* (make-string-output-stream))

(defun reset ()
  (setf *passed* 0 *failed* 0 *out* (make-string-output-stream) *err* (make-string-output-stream)))

(defun check (name ok &optional detail)
  (if ok
      (incf *passed*)
      (progn
        (incf *failed*)
        (format t "FAIL ~a~@[~%~a~]~%" name detail)))
  ok)

(defun check-equal (name actual expected)
  (check name (equalp actual expected)
         (format nil "  got      ~s~%  expected ~s" actual expected)))

(defun check-text (name actual expected)
  (check name (string= actual expected)
         (format nil "  got      ~s~%  expected ~s" actual expected)))

(defun report ()
  (format t "checks: ~d, passed: ~d, failed: ~d~%" (+ *passed* *failed*) *passed* *failed*)
  (if (zerop *failed*) 0 1))

(defun captured-out () (get-output-stream-string *out*))
(defun captured-err () (get-output-stream-string *err*))

(defun null-io (&key read-file read-stdin)
  "An io whose writers collect into the harness buffers."
  (textstat.runner:make-io
   :read-file read-file
   :read-stdin read-stdin
   :out (lambda (text) (write-string text *out*))
   :err (lambda (text) (write-string text *err*))))

(defparameter *root*
  ;; tests/harness.lisp lives one directory below the project root.
  (merge-pathnames (make-pathname :directory '(:relative :up))
                   (make-pathname :name nil :type nil :defaults *load-truename*)))

(defun fixture-path (name)
  (merge-pathnames (format nil "tests/.tmp/~a" name) *root*))

(defun fixture-bytes (name bytes)
  "Write BYTES (a list of byte values) to a fixture and return its pathname."
  (let ((path (fixture-path name)))
    (ensure-directories-exist path)
    (with-open-file (out path :direction :output :element-type '(unsigned-byte 8)
                              :if-exists :supersede)
      (write-sequence (make-array (length bytes) :element-type '(unsigned-byte 8)
                                                 :initial-contents bytes)
                      out))
    path))

(defun read-file-bytes (path)
  (with-open-file (in path :element-type '(unsigned-byte 8))
    (let ((buffer (make-array 0 :element-type '(unsigned-byte 8) :adjustable t :fill-pointer 0))
          (chunk (make-array 4096 :element-type '(unsigned-byte 8))))
      (loop for count = (read-sequence chunk in)
            while (plusp count)
            do (loop for i from 0 below count do (vector-push-extend (aref chunk i) buffer)))
      (coerce buffer '(simple-array (unsigned-byte 8) (*))))))

(defun bytes->list (vector) (coerce vector 'list))

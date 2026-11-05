;;;; A test harness small enough to read: no framework, no dependency.
(defpackage :textstat.harness
  (:use :cl)
  (:export #:reset #:check #:check-text #:check-equal #:report))

(in-package :textstat.harness)

(defvar *passed* 0)
(defvar *failed* 0)

(defun reset ()
  (setf *passed* 0 *failed* 0))

(defun check (name ok &optional detail)
  (if ok
      (incf *passed*)
      (progn
        (incf *failed*)
        (format t "FAIL ~A~@[~%~A~]~%" name detail)))
  ok)

(defun check-text (name actual expected)
  (check name (string= actual expected)
         (format nil "  got      ~S~%  expected ~S" actual expected)))

(defun check-equal (name actual expected)
  (check name (equalp actual expected)
         (format nil "  got      ~S~%  expected ~S" actual expected)))

(defun report ()
  (format t "checks: ~D, passed: ~D, failed: ~D~%" (+ *passed* *failed*) *passed* *failed*)
  (if (zerop *failed*) 0 1))

;;;; Minimal harness.
(defpackage :lisp-json.harness
  (:use :cl)
  (:export #:reset #:check #:check-text #:report))
(in-package :lisp-json.harness)
(defvar *passed* 0)
(defvar *failed* 0)
(defun reset () (setf *passed* 0 *failed* 0))
(defun check (name ok &optional detail)
  (if ok (incf *passed*) (progn (incf *failed*) (format t "FAIL ~a~@[~%~a~]~%" name detail)))
  ok)
(defun check-text (name actual expected)
  (check name (string= actual expected) (format nil "got ~s expected ~s" actual expected)))
(defun report () (format t "checks: ~d, passed: ~d, failed: ~d~%" (+ *passed* *failed*) *passed* *failed*) (if (zerop *failed*) 0 1))

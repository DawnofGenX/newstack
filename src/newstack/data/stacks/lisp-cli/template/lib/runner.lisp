;;;; The program, with every effect injected so the whole contract is testable.
(defpackage :textstat.runner
  (:use :cl)
  (:export #:io #:make-io #:io-read-file #:io-read-stdin #:io-out #:io-err
           #:program #:run))

(in-package :textstat.runner)

(defstruct (io (:constructor make-io (&key read-file read-stdin out err)))
  (read-file nil)
  (read-stdin nil)
  (out nil)
  (err nil))

(defparameter *program* "{{ npm_name }}")

(defun program () *program*)

(defun width-of (rows)
  "One width for every printed row, so the columns line up like wc's."
  (let ((width 1))
    (dolist (row rows width)
      (dolist (value (first row))
        (setf width (max width (length (princ-to-string value))))))))

(defun render-row (values label width)
  (with-output-to-string (out)
    (loop for (value . rest) on values
          do (format out "~vd" width value)
             (if rest (write-char #\Space out) (when label (write-char #\Space out))))
    (when label (princ label out))))

(defun read-bytes (io path)
  "The bytes of PATH, or NIL when it cannot be read."
  (handler-case
      (funcall (io-read-file io) path)
    (error () nil)))

(defun read-standard-input (io)
  (handler-case
      (funcall (io-read-stdin io))
    (error () nil)))

(defun complain (io path)
  (funcall (io-err io) (format nil "~a: cannot open '~a'~%" (program) path)))

(defun run (args io)
  (let ((parsed (textstat.options:parse-args args)))
    (case (textstat.options:parsed-status parsed)
      (:help
       (funcall (io-out io) (textstat.options:usage (program)))
       0)
      (:version
       (funcall (io-out io) (format nil "~a~%" (textstat.options:tool-version)))
       0)
      (:usage-error
       (funcall (io-err io)
                (format nil "~a: ~a~%" (program) (textstat.options:parsed-message parsed)))
       (funcall (io-err io)
                (format nil "Try '~a --help' for more information.~%" (program)))
       2)
      (otherwise
       (let* ((figures (textstat.options:parsed-figures parsed))
              (operands (or (textstat.options:parsed-files parsed) (list "-")))
              (rows '())
              (total (textstat.counts:empty))
              (failed nil))
         (dolist (operand operands)
           (let ((data (if (string= operand "-")
                           (read-standard-input io)
                           (read-bytes io operand))))
             (if (null data)
                 (progn
                   (setf failed t)
                   (unless (string= operand "-") (complain io operand)))
                 (let ((tally (textstat.counts:of-bytes data)))
                   (setf total (textstat.counts:add total tally))
                   (push (list (textstat.counts:column-values figures tally)
                               (if (string= operand "-") "-" operand))
                         rows)))))
         (setf rows (nreverse rows))
         (when (> (length operands) 1)
           (setf rows (append rows
                              (list (list (textstat.counts:column-values figures total)
                                          "total")))))
         (let ((width (width-of rows)))
           (dolist (row rows)
             (funcall (io-out io)
                      (format nil "~a~%" (render-row (first row) (second row) width)))))
         (if failed 1 0))))))

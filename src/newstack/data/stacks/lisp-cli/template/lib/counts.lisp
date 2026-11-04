;;;; Byte-exact counting: the part of the program that must agree with wc.
(defpackage :textstat.counts
  (:use :cl)
  (:export #:counts #:make-counts #:counts-lines #:counts-words #:counts-bytes
           #:empty #:add #:is-space-byte #:of-bytes #:column-values))

(in-package :textstat.counts)

(defstruct (counts (:constructor make-counts (lines words bytes)))
  (lines 0 :type integer)
  (words 0 :type integer)
  (bytes 0 :type integer))

(defun empty ()
  (make-counts 0 0 0))

;;; wc uses isspace(3): space, tab, newline, vertical tab, form feed, carriage return.
(defun is-space-byte (byte)
  (or (= byte 32) (= byte 9) (= byte 10) (= byte 13) (= byte 11) (= byte 12)))

(defun of-bytes (data)
  "Count DATA, a vector with element type (unsigned-byte 8)."
  (let ((lines 0)
        (words 0)
        (in-word nil))
    (loop for byte across data
          do (cond ((= byte 10)
                    (incf lines)
                    (setf in-word nil))
                   ((is-space-byte byte)
                    (setf in-word nil))
                   (t
                    (unless in-word
                      (incf words)
                      (setf in-word t)))))
    (make-counts lines words (length data))))

(defun add (left right)
  (make-counts (+ (counts-lines left) (counts-lines right))
               (+ (counts-words left) (counts-words right))
               (+ (counts-bytes left) (counts-bytes right))))

(defun column-values (figures tally)
  "The figures in wc's order, as a list of integers."
  (loop for figure in figures
        collect (ecase figure
                  (:lines (counts-lines tally))
                  (:words (counts-words tally))
                  (:bytes (counts-bytes tally)))))

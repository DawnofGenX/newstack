;;;; Counting: the same rules wc uses, over the UTF-8 bytes of the string.
(defpackage :textstat.counts
  (:use :cl)
  (:export #:counts #:make-counts #:counts-lines #:counts-words #:counts-bytes
           #:count-text #:is-space))

(in-package :textstat.counts)

(defstruct (counts (:constructor make-counts (lines words bytes)))
  (lines 0 :type integer)
  (words 0 :type integer)
  (bytes 0 :type integer))

(defun is-space (character)
  (member character '(#\Space #\Tab #\Newline #\Return (code-char 11) (code-char 12))))

(defun count-text (text)
  "Count TEXT: a line is a newline, a word is a maximal run of non-space
characters, bytes are the length of the UTF-8 encoding."
  (unless (stringp text)
    (error "count-text expects a string, got ~S" (type-of text)))
  (let ((lines 0)
        (words 0)
        (in-word nil))
    (loop for character across text
          do (cond
               ((char= character #\Newline) (incf lines) (setf in-word nil))
               ((is-space character) (setf in-word nil))
               ((not in-word) (incf words) (setf in-word t))))
    (make-counts lines words
                 (length (sb-ext:string-to-octets text :external-format :utf-8)))))

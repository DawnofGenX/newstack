;;;; What must agree with wc.
(in-package :textstat.harness)

(defun counts-tests ()
  (let* ((plain (fixture-bytes "plain.txt" '(97 108 112 104 97 32 98 101 116 97 10
                                             103 97 109 109 97 32 100 101 108 116 97 10)))
         (notrail (fixture-bytes "notrail.txt" '(97 108 112 104 97 32 98 101 116 97 10
                                                 103 97 109 109 97 32 100 101 108 116 97)))
         (utf8 (fixture-bytes "utf8.txt" '(104 195 169 108 108 111 32 119 195 182 114 108 100 10)))
         (empty (fixture-bytes "empty.txt" '()))
         (control (fixture-bytes "control.txt" '(97 9 98 11 99 12 100 10)))
         (count-of (lambda (path) (textstat.counts:of-bytes (read-file-bytes path)))))
    (let ((plain-counts (funcall count-of plain)))
      (check-equal "plain: lines" (textstat.counts:counts-lines plain-counts) 2)
      (check-equal "plain: words" (textstat.counts:counts-words plain-counts) 4)
      (check-equal "plain: bytes" (textstat.counts:counts-bytes plain-counts) 23))
    (let ((notrail-counts (funcall count-of notrail)))
      (check-equal "no trailing newline: lines" (textstat.counts:counts-lines notrail-counts) 1)
      (check-equal "no trailing newline: words" (textstat.counts:counts-words notrail-counts) 4)
      (check-equal "no trailing newline: bytes" (textstat.counts:counts-bytes notrail-counts) 22))
    (let ((utf8-counts (funcall count-of utf8)))
      (check-equal "utf-8 counts bytes, not characters"
                   (textstat.counts:counts-bytes utf8-counts) 14)
      (check-equal "utf-8 words" (textstat.counts:counts-words utf8-counts) 2))
    (let ((empty-counts (funcall count-of empty)))
      (check-equal "empty: lines" (textstat.counts:counts-lines empty-counts) 0)
      (check-equal "empty: bytes" (textstat.counts:counts-bytes empty-counts) 0))
    (let ((control-counts (funcall count-of control)))
      (check-equal "tab, vertical tab and form feed separate words"
                   (textstat.counts:counts-words control-counts) 4)
      (check-equal "control fixture bytes" (textstat.counts:counts-bytes control-counts) 8))
    (check-equal "every space character is a separator"
                 (mapcar #'textstat.counts:is-space-byte '(32 9 10 13 11 12)) '(t t t t t t))
    (check-equal "a letter is not a separator"
                 (textstat.counts:is-space-byte 65) nil)
    (check-equal "adding tallies adds every field"
                 (textstat.counts:column-values '(:lines :words :bytes)
                                                (textstat.counts:add
                                                 (textstat.counts:make-counts 1 2 3)
                                                 (textstat.counts:make-counts 4 5 6)))
                 '(5 7 9))
    (check-equal "the empty tally is all zeroes"
                 (textstat.counts:column-values '(:lines :words :bytes)
                                                (textstat.counts:empty))
                 '(0 0 0))
    (check-equal "columns follow the requested figures"
                 (textstat.counts:column-values '(:bytes :lines) (textstat.counts:make-counts 7 8 9))
                 '(9 7))
    (check-equal "a single newline is one line" 
                 (textstat.counts:counts-lines
                  (textstat.counts:of-bytes (make-array 1 :element-type '(unsigned-byte 8)
                                                          :initial-contents '(10))))
                 1)
    (check-equal "no newline means no lines"
                 (textstat.counts:counts-lines
                  (textstat.counts:of-bytes (make-array 2 :element-type '(unsigned-byte 8)
                                                          :initial-contents '(97 98))))
                 0)))

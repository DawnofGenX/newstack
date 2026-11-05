;;;; A small, strict JSON reader: an object of scalars, nothing else.
;;;;
;;;; Values come back as conses so that a number never turns into a string:
;;;;   (:string . "42")   (:number . "42")   (:literal . "true")
;;;; The whole document is (values :object ALIST) where ALIST maps string
;;;; keys to those conses. Anything that is not JSON signals JSON-ERROR.
(defpackage :textstat.json
  (:use :cl)
  (:export #:json-error #:decode #:value-kind #:value-text))

(in-package :textstat.json)

(define-condition json-error (error)
  ((detail :initarg :detail :reader json-error-detail))
  (:report (lambda (condition stream)
             (format stream "bad json: ~A" (json-error-detail condition)))))

(defstruct (cursor (:constructor make-cursor (text)))
  (text "" :type string)
  (index 0 :type fixnum))

(defun fail (cursor message)
  (error 'json-error :detail (format nil "~A at byte ~D" message (cursor-index cursor))))

(defun peek (cursor)
  (let ((i (cursor-index cursor)))
    (if (< i (length (cursor-text cursor)))
        (char (cursor-text cursor) i)
        nil)))

(defun skip-space (cursor)
  (loop while (let ((c (peek cursor)))
                (and c (member c '(#\Space #\Tab #\Newline #\Return))))
        do (incf (cursor-index cursor)))
  cursor)

(defun expect (cursor character)
  (if (and (peek cursor) (char= (peek cursor) character))
      (incf (cursor-index cursor))
      (fail cursor "unexpected character")))

(defun parse-string (cursor)
  (expect cursor #\")
  (let ((out (make-string-output-stream)))
    (loop
      (let ((c (peek cursor)))
        (cond
          ((null c) (fail cursor "unterminated string"))
          ((char= c #\") (incf (cursor-index cursor)) (return (get-output-stream-string out)))
          ((char= c #\\)
           (incf (cursor-index cursor))
           (let ((escape (peek cursor)))
             (incf (cursor-index cursor))
             (case escape
               (#\" (write-char #\" out))
               (#\\ (write-char #\\ out))
               (#\/ (write-char #\/ out))
               (#\b (write-char (code-char 8) out))
               (#\f (write-char (code-char 12) out))
               (#\n (write-char #\Newline out))
               (#\r (write-char #\Return out))
               (#\t (write-char #\Tab out))
               (#\u (let ((code (parse-integer (subseq (cursor-text cursor)
                                                      (cursor-index cursor)
                                                      (min (+ (cursor-index cursor) 4)
                                                           (length (cursor-text cursor))))
                                              :radix 16
                                              :junk-allowed t)))
                      (unless code (fail cursor "bad escape"))
                      (incf (cursor-index cursor) 4)
                      (write-char (code-char code) out)))
               (t (fail cursor "unknown escape")))))
          ((char< c (code-char 32)) (fail cursor "control character in string"))
          (t (write-char c out) (incf (cursor-index cursor))))))))

(defun parse-number (cursor)
  (let ((start (cursor-index cursor)))
    (loop while (let ((c (peek cursor)))
                  (and c (or (digit-char-p c) (member c '(#\- #\+ #\. #\e #\E)))))
          do (incf (cursor-index cursor)))
    (if (= start (cursor-index cursor))
        (fail cursor "expected a number")
        (subseq (cursor-text cursor) start (cursor-index cursor)))))

(defun parse-value (cursor)
  (skip-space cursor)
  (let ((c (peek cursor)))
    (cond
      ((null c) (fail cursor "unexpected end of input"))
      ((char= c #\") (cons :string (parse-string cursor)))
      ((char= c #\{) (parse-object cursor))
      ((member c '(#\- #\0 #\1 #\2 #\3 #\4 #\5 #\6 #\7 #\8 #\9))
       (cons :number (parse-number cursor)))
      (t
       (let ((rest (subseq (cursor-text cursor) (cursor-index cursor))))
         (cond
           ((and (>= (length rest) 4) (string= (subseq rest 0 4) "true"))
            (incf (cursor-index cursor) 4) (cons :literal "true"))
           ((and (>= (length rest) 5) (string= (subseq rest 0 5) "false"))
            (incf (cursor-index cursor) 5) (cons :literal "false"))
           ((and (>= (length rest) 4) (string= (subseq rest 0 4) "null"))
            (incf (cursor-index cursor) 4) (cons :literal "null"))
           (t (fail cursor "unexpected character"))))))))

(defun parse-object (cursor)
  (expect cursor #\{)
  (let ((alist '()))
    (skip-space cursor)
    (when (and (peek cursor) (char= (peek cursor) #\}))
      (incf (cursor-index cursor))
      (return-from parse-object (cons :object (nreverse alist))))
    (loop
      (skip-space cursor)
      (let ((key (parse-string cursor)))
        (skip-space cursor)
        (expect cursor #\:)
        (push (cons key (parse-value cursor)) alist))
      (skip-space cursor)
      (cond
        ((and (peek cursor) (char= (peek cursor) #\,)) (incf (cursor-index cursor)))
        ((and (peek cursor) (char= (peek cursor) #\})) (incf (cursor-index cursor)) (return))
        (t (fail cursor "expected , or }"))))
    (cons :object (nreverse alist))))

(defun decode (text)
  "Parse TEXT as JSON. Returns (values KIND VALUE); signals JSON-ERROR."
  (let* ((cursor (make-cursor text))
         (value (parse-value cursor)))
    (skip-space cursor)
    (when (< (cursor-index cursor) (length text))
      (fail cursor "trailing data"))
    (values (car value) (cdr value))))

(defun value-kind (value)
  (and (consp value) (car value)))

(defun value-text (value)
  (and (consp value) (cdr value)))

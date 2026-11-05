;;;; The contract: four strings in, a status code and a JSON body out.
;;;; Nothing here knows about sockets, so every status code is testable.
(load (merge-pathnames "json.lisp"
                       (make-pathname :name nil :type nil
                                      :defaults (or *load-truename* *default-pathname-defaults*))))
(load (merge-pathnames "counts.lisp"
                       (make-pathname :name nil :type nil
                                      :defaults (or *load-truename* *default-pathname-defaults*))))

(defpackage :textstat.contract
  (:use :cl)
  (:export #:reply #:reply-status #:reply-body #:route))

(in-package :textstat.contract)

(defstruct (reply (:constructor make-reply (status body)))
  (status 200 :type integer)
  (body "" :type string))

(defun json-quote (text)
  "Quote TEXT for a JSON string: control characters become \\u00XX."
  (with-output-to-string (out)
    (write-char #\" out)
    (loop for character across text
          do (let ((code (char-code character)))
               (case character
                 (#\" (write-string "\\\"" out))
                 (#\\ (write-string "\\\\" out))
                 (#\Newline (write-string "\\n" out))
                 (#\Return (write-string "\\r" out))
                 (#\Tab (write-string "\\t" out))
                 (t (if (< code 32)
                        (format out "\\u~4,'0X" code)
                        (write-char character out))))))
    (write-char #\" out)))

(defun counts-json (text counts)
  (format nil "{\"text\":~A,\"lines\":~D,\"words\":~D,\"bytes\":~D}"
          (json-quote text)
          (textstat.counts:counts-lines counts)
          (textstat.counts:counts-words counts)
          (textstat.counts:counts-bytes counts)))

(defun error-reply (status code &optional detail)
  (make-reply status
              (if detail
                  (format nil "{\"error\":~A,\"detail\":~A}"
                          (json-quote code) (json-quote detail))
                  (format nil "{\"error\":~A}" (json-quote code)))))

(defun percent-decode (raw)
  (with-output-to-string (out)
    (loop with i = 0
          while (< i (length raw))
          do (let ((c (char raw i)))
               (cond
                 ((char= c #\+) (write-char #\Space out) (incf i))
                 ((and (char= c #\%) (< (+ i 2) (length raw)))
                  (let ((hex (subseq raw (1+ i) (+ i 3))))
                    (if (every (lambda (h) (digit-char-p h 16)) hex)
                        (progn (write-char (code-char (parse-integer hex :radix 16)) out)
                               (incf i 3))
                        (progn (write-char c out) (incf i)))))
                 (t (write-char c out) (incf i)))))))

(defun split-pair (pair)
  "Split \"key=value\" on the first equals; a missing equals gives a nil value."
  (let ((equals (position #\= pair)))
    (if equals
        (values (subseq pair 0 equals) (subseq pair (1+ equals)))
        (values pair nil))))

(defun split-on (text character)
  "Split TEXT on every CHARACTER; empty pieces are dropped."
  (let ((pieces '())
        (start 0))
    (loop for i from 0 below (length text)
          when (char= (char text i) character)
            do (when (> i start) (push (subseq text start i) pieces))
               (setf start (1+ i)))
    (when (> (length text) start) (push (subseq text start) pieces))
    (nreverse pieces)))

(defun query-param (query name)
  "Return (values VALUE PRESENT) for NAME in a raw query string."
  (loop for pair in (split-on query #\&)
        when (plusp (length pair))
          do (multiple-value-bind (key value) (split-pair pair)
               (when (string= (percent-decode key) name)
                 (return-from query-param (values (percent-decode (or value "")) t))))
        finally (return (values nil nil))))

(defun body-field (body)
  "Return (:invalid), (:missing) or (:text VALUE) for a posted body."
  (handler-case
      (multiple-value-bind (kind value) (textstat.json:decode body)
        (if (eq kind :object)
            (let ((entry (cdr (assoc "text" value :test #'string=))))
              (cond
                ((null entry) (list :missing))
                ((eq (textstat.json:value-kind entry) :string) (list :text (textstat.json:value-text entry)))
                (t (list :missing))))
            (list :missing)))
    (textstat.json:json-error () (list :invalid))))

(defun route (method path query body)
  "Answer a request. METHOD is uppercase (\"GET\"), QUERY is raw, BODY is a string."
  (cond
    ((and (string= method "GET") (string= path "/health"))
     (make-reply 200 "{\"status\":\"ok\"}"))
    ((and (string= method "GET") (string= path "/stats"))
     (multiple-value-bind (text present) (query-param query "text")
       (if present
           (make-reply 200 (counts-json text (textstat.counts:count-text text)))
           (error-reply 422 "missing_text"))))
    ((and (string= method "POST") (string= path "/stats"))
     (let ((field (body-field body)))
       (case (first field)
         (:invalid (error-reply 422 "invalid_json"))
         (:missing (error-reply 422 "missing_text"))
         (:text (make-reply 200 (counts-json (second field)
                                             (textstat.counts:count-text (second field))))))))
    ((member path '("/health" "/stats") :test #'string=)
     (error-reply 405 "method_not_allowed"))
    (t (error-reply 404 "not_found" (format nil "no route for ~A ~A" method path)))))

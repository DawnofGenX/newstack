;;;; Entry point: load the library, run every check, report, exit.
(let ((here (merge-pathnames (make-pathname :directory '(:relative :up))
                             (make-pathname :name nil :type nil :defaults *load-truename*))))
  (load (merge-pathnames "lib/contract.lisp" here))
  (load (merge-pathnames "tests/harness.lisp" here)))

(in-package :textstat.harness)

(defun counts-equal (text lines words bytes)
  (let ((counts (textstat.counts:count-text text)))
    (and (= (textstat.counts:counts-lines counts) lines)
         (= (textstat.counts:counts-words counts) words)
         (= (textstat.counts:counts-bytes counts) bytes))))

(defun counts-detail (text)
  (let ((counts (textstat.counts:count-text text)))
    (format nil "  got      ~D/~D/~D~%  expected another table row"
            (textstat.counts:counts-lines counts)
            (textstat.counts:counts-words counts)
            (textstat.counts:counts-bytes counts))))

(defun reply-of (method path query body)
  (textstat.contract:route method path query body))

(defun status-of (method path query body)
  (textstat.contract:reply-status (reply-of method path query body)))

(defun body-of (method path query body)
  (textstat.contract:reply-body (reply-of method path query body)))

(defun counts-tests ()
  (check "hello world" (counts-equal (format nil "hello world~%") 1 2 12)
         (counts-detail (format nil "hello world~%")))
  (check "empty" (counts-equal "" 0 0 0) (counts-detail ""))
  (check "blank lines" (counts-equal (format nil "~%~%x~%") 3 1 4)
         (counts-detail (format nil "~%~%x~%")))
  (check "spaces and tabs" (counts-equal (format nil "  ~C " #\Tab) 0 0 4)
         (counts-detail (format nil "  ~C " #\Tab)))
  (check "no trailing newline" (counts-equal "abc" 0 1 3) (counts-detail "abc"))
  (check "utf-8 is counted in bytes"
         (counts-equal (format nil "h~Cllo w~Crld~%" #\é #\ö) 1 2 14)
         (counts-detail (format nil "h~Cllo w~Crld~%" #\é #\ö)))
  (check "an emoji is four bytes"
         (counts-equal (format nil "~C~%" #\🙂) 1 1 5)
         (counts-detail (format nil "~C~%" #\🙂)))
  (check "a non-string is refused"
         (handler-case (progn (textstat.counts:count-text 42) nil)
           (error () t))))

(defun json-tests ()
  (multiple-value-bind (kind value) (textstat.json:decode "{\"text\":\"a\"}")
    (check "an object decodes" (eq kind :object))
    (check "the field keeps its kind"
           (eq (textstat.json:value-kind (cdr (assoc "text" value :test #'string=))) :string)))
  (multiple-value-bind (kind value) (textstat.json:decode "{\"text\":42}")
    (check "a number is not a string"
           (eq (textstat.json:value-kind (cdr (assoc "text" value :test #'string=))) :number))
    (check "numbers keep their raw text"
           (string= (textstat.json:value-text (cdr (assoc "text" value :test #'string=))) "42")))
  (check "escapes are decoded"
         (string= (textstat.json:value-text
                   (cdr (assoc "text" (nth-value 1 (textstat.json:decode "{\"text\":\"a\\nb\"}"))
                               :test #'string=)))
                  (format nil "a~%b")))
  (check "a bare word is not json"
         (handler-case (progn (textstat.json:decode "nope") nil)
           (textstat.json:json-error () t)))
  (check "trailing data is refused"
         (handler-case (progn (textstat.json:decode "{\"text\":\"a\"} junk") nil)
           (textstat.json:json-error () t))))

(defparameter +newline-escape+
  ;; The two characters backslash and n, which is what JSON puts on the wire
  ;; for a newline inside a string. A Lisp string literal cannot spell it, so
  ;; build it from characters.
  (coerce (list #\\ #\n) 'string))

(defun contract-tests ()
  (check-text "health" (body-of "GET" "/health" "" "") "{\"status\":\"ok\"}")
  (check "health is 200" (= 200 (status-of "GET" "/health" "" "")))
  (check-text "a query is counted"
              (body-of "GET" "/stats" "text=hello%20world%0A" "")
              (concatenate 'string
                           "{\"text\":\"hello world" +newline-escape+
                           "\",\"lines\":1,\"words\":2,\"bytes\":12}"))
  (check "an empty query value is a value" (= 200 (status-of "GET" "/stats" "text=" "")))
  (check-text "an empty query counts zero"
              (body-of "GET" "/stats" "text=" "")
              "{\"text\":\"\",\"lines\":0,\"words\":0,\"bytes\":0}")
  (check "a missing query is 422" (= 422 (status-of "GET" "/stats" "" "")))
  (check-text "a missing query says so"
              (body-of "GET" "/stats" "" "") "{\"error\":\"missing_text\"}")
  (check-text "a posted body is counted"
              (body-of "POST" "/stats" ""
                       (concatenate 'string
                                    "{\"text\":\"a b" +newline-escape+
                                    "c" +newline-escape+ "\"}"))
              (concatenate 'string
                           "{\"text\":\"a b" +newline-escape+
                           "c" +newline-escape+
                           "\",\"lines\":2,\"words\":3,\"bytes\":6}"))
  (check "a number is not text" (= 422 (status-of "POST" "/stats" "" "{\"text\":42}")))
  (check "a quoted number is text" (= 200 (status-of "POST" "/stats" "" "{\"text\":\"42\"}")))
  (check "a body that is not json is 422" (= 422 (status-of "POST" "/stats" "" "nope")))
  (check-text "a body that is not json says so"
              (body-of "POST" "/stats" "" "nope") "{\"error\":\"invalid_json\"}")
  (check "another method is 405" (= 405 (status-of "DELETE" "/health" "" "")))
  (check-text "another method says so"
              (body-of "PUT" "/stats" "" "") "{\"error\":\"method_not_allowed\"}")
  (check "an unknown route is 404" (= 404 (status-of "GET" "/nope" "" "")))
  (check-text "an unknown route names it"
              (body-of "GET" "/nope" "" "")
              "{\"error\":\"not_found\",\"detail\":\"no route for GET /nope\"}")
  (check "a plus is a space in a query"
         (string= (textstat.contract:reply-body
                   (textstat.contract:route "GET" "/stats" "text=a+b" ""))
                  "{\"text\":\"a b\",\"lines\":0,\"words\":2,\"bytes\":3}")))

(textstat.harness:reset)
(textstat.harness::counts-tests)
(textstat.harness::json-tests)
(textstat.harness::contract-tests)
(sb-ext:exit :code (textstat.harness:report))

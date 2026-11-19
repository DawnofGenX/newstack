(load (merge-pathnames "../lib/json.lisp" *load-truename*))

(defvar *failures* 0)

(defun check (name ok)
  (if ok
      (format t "ok   ~a~%" name)
      (progn (incf *failures*) (format t "FAIL ~a~%" name))))

(defun assert-equal (name actual expected)
  (check name (equal actual expected)))

;; Pinned known values
(assert-equal "dot path"
  (jsonpath.json:eval-path (jsonpath.json:parse-json "{\"a\":{\"b\":42}}") "$.a.b")
  '(42))

(assert-equal "array star"
  (jsonpath.json:eval-path (jsonpath.json:parse-json "{\"arr\":[1,2,3]}") "$.arr[*]")
  '(1 2 3))

(assert-equal "recursive descent"
  (jsonpath.json:eval-path (jsonpath.json:parse-json "{\"deep\":{\"x\":{\"y\":\"z\"}}}") "$..y")
  '("z"))

(assert-equal "format number"
  (jsonpath.json:format-json 42)
  "42")

(assert-equal "format string"
  (jsonpath.json:format-json "hi")
  "\"hi\"")

;; Error case: malformed JSON must signal an error.
(let ((signaled nil))
  (handler-case
      (jsonpath.json:parse-json "{\"a\":")
    (error () (setf signaled t)))
  (check "malformed json signals" signaled))

(format t "failures: ~d~%" *failures*)
(if (zerop *failures*)
    (sb-ext:exit :code 0)
    (sb-ext:exit :code 1))
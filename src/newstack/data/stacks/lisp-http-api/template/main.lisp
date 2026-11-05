;;;; textstat — the only file that reads the environment and blocks.
(load (merge-pathnames "lib/server.lisp"
                       (make-pathname :name nil :type nil :defaults *load-truename*)))

(defun env-or (name fallback)
  (let ((value (sb-ext:posix-getenv name)))
    (if (and value (plusp (length value))) value fallback)))

(defun main ()
  (textstat.server:serve (env-or "HOST" "127.0.0.1")
                         (parse-integer (env-or "PORT" "8080"))))

(main)

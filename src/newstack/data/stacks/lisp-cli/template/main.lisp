;;;; textstat — the only file that touches the real process.
(load (merge-pathnames "lib/counts.lisp" (make-pathname :name nil :type nil :defaults *load-truename*)))
(load (merge-pathnames "lib/options.lisp" (make-pathname :name nil :type nil :defaults *load-truename*)))
(load (merge-pathnames "lib/runner.lisp" (make-pathname :name nil :type nil :defaults *load-truename*)))

(defun read-path (path)
  (with-open-file (in path :element-type '(unsigned-byte 8) :if-does-not-exist :error)
    (let ((buffer (make-array 0 :element-type '(unsigned-byte 8) :adjustable t :fill-pointer 0))
          (chunk (make-array 65536 :element-type '(unsigned-byte 8))))
      (loop for count = (read-sequence chunk in)
            while (plusp count)
            do (loop for i from 0 below count
                     do (vector-push-extend (aref chunk i) buffer)))
      (coerce buffer '(simple-array (unsigned-byte 8) (*))))))

(defun read-standard-input ()
  (with-open-file (in "/dev/stdin" :element-type '(unsigned-byte 8))
    (let ((buffer (make-array 0 :element-type '(unsigned-byte 8) :adjustable t :fill-pointer 0))
          (chunk (make-array 65536 :element-type '(unsigned-byte 8))))
      (loop for count = (read-sequence chunk in)
            while (plusp count)
            do (loop for i from 0 below count
                     do (vector-push-extend (aref chunk i) buffer)))
      (coerce buffer '(simple-array (unsigned-byte 8) (*))))))

(defun main ()
  (let ((io (textstat.runner:make-io
             :read-file #'read-path
             :read-stdin #'read-standard-input
             :out (lambda (text) (write-string text) (finish-output))
             :err (lambda (text) (write-string text *error-output*) (finish-output *error-output*)))))
    (let ((code (textstat.runner:run (cdr sb-ext:*posix-argv*) io)))
      (finish-output)
      (sb-ext:exit :code code))))

(main)

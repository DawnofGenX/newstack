;;;; The socket: read one HTTP/1.1 request, ask the contract, write the answer.
;;;; SBCL ships sb-bsd-sockets, so there is still no dependency to install.
(load (merge-pathnames "contract.lisp"
                       (make-pathname :name nil :type nil
                                      :defaults (or *load-truename* *default-pathname-defaults*))))

(require :sb-bsd-sockets)

(defpackage :textstat.server
  (:use :cl)
  (:export #:serve #:handle-request #:parse-request))

(in-package :textstat.server)

(defparameter *max-header-bytes* 8192)
(defparameter *max-body-bytes* 65536)

(defstruct (request (:constructor make-request (method path query body)))
  (method "GET" :type string)
  (path "/" :type string)
  (query "" :type string)
  (body "" :type string))

(defun ends-with-blank-line (buffer)
  "True when the last four bytes are CRLFCRLF."
  (let ((n (fill-pointer buffer)))
    (and (>= n 4)
         (= (aref buffer (- n 4)) 13)
         (= (aref buffer (- n 3)) 10)
         (= (aref buffer (- n 2)) 13)
         (= (aref buffer (- n 1)) 10))))

(defun read-until-blank-line (stream)
  "Read bytes until the CRLFCRLF that ends the header block. Returns a string."
  (let ((buffer (make-array 0 :element-type '(unsigned-byte 8) :adjustable t :fill-pointer 0))
        (byte 0))
    (loop
      (setf byte (read-byte stream nil nil))
      (when (null byte) (return (values (map 'string #'code-char buffer) nil)))
      (vector-push-extend byte buffer)
      (when (ends-with-blank-line buffer)
        (return (values (map 'string #'code-char buffer) t)))
      (when (> (fill-pointer buffer) *max-header-bytes*)
        (return (values (map 'string #'code-char buffer) nil))))))

(defun split-header-block (text)
  "Split a header block into its lines, dropping the CRs and the blank tail."
  (let ((lines '())
        (start 0))
    (loop for i from 0 below (length text)
          when (and (char= (char text i) #\Return)
                    (< (1+ i) (length text))
                    (char= (char text (1+ i)) #\Newline))
            do (push (subseq text start i) lines)
               (setf start (+ i 2))
               (incf i))
    (when (> (length text) start) (push (subseq text start) lines))
    (remove "" (nreverse lines) :test #'string=)))

(defun header-value (headers name)
  (cdr (assoc name headers :test #'string=)))

(defun parse-request-line (line)
  (let* ((first-space (position #\Space line))
         (last-space (position #\Space line :from-end t)))
    (when (or (null first-space) (null last-space) (= first-space last-space))
      (return-from parse-request-line nil))
    (let ((method (subseq line 0 first-space))
          (target (subseq line (1+ first-space) last-space)))
      (let ((question (position #\? target)))
        (values method
                (if question (subseq target 0 question) target)
                (if question (subseq target (1+ question)) ""))))))

(defun parse-request (header-text body)
  "Turn a header block and a body into a REQUEST. Signals a string on garbage."
  (let ((lines (split-header-block header-text)))
    (multiple-value-bind (method path query) (parse-request-line (or (first lines) ""))
      (unless method (error "malformed request line"))
      (make-request (string-upcase method) path query body))))

(defun reason-phrase (status)
  (case status
    (200 "OK")
    (404 "Not Found")
    (405 "Method Not Allowed")
    (413 "Payload Too Large")
    (422 "Unprocessable Entity")
    (t "Internal Server Error")))

(defun header-pairs (header-text)
  (loop for line in (rest (split-header-block header-text))
        for colon = (position #\: line)
        when colon
          collect (cons (string-downcase (string-trim '(#\Space #\Tab) (subseq line 0 colon)))
                        (string-trim '(#\Space #\Tab) (subseq line (1+ colon))))))

(defun read-body (stream headers)
  (let ((length-text (header-value headers "content-length")))
    (if (null length-text)
        ""
        (let* ((length (parse-integer length-text :junk-allowed t))
               (size (or length 0)))
          (when (> size *max-body-bytes*)
            (return-from read-body :too-large))
          (let ((bytes (make-array size :element-type '(unsigned-byte 8))))
            (loop with offset = 0
                  while (< offset size)
                  do (let ((count (read-sequence bytes stream :start offset)))
                       (if (zerop count)
                           (return)
                           (setf offset count))))
            (map 'string #'code-char bytes))))))

(defun write-response (stream status body)
  "Write one HTTP/1.1 response. STREAM is binary, so the header goes out as bytes."
  (let* ((payload (map '(vector (unsigned-byte 8)) #'char-code body))
         (header (format nil
                         "HTTP/1.1 ~D ~A~C~CContent-Type: application/json~C~CContent-Length: ~D~C~CConnection: close~C~C~C~C"
                         status (reason-phrase status) #\Return #\Newline
                         #\Return #\Newline
                         (length payload)
                         #\Return #\Newline
                         #\Return #\Newline #\Return #\Newline))
         (head (map '(vector (unsigned-byte 8)) #'char-code header)))
    (write-sequence head stream)
    (write-sequence payload stream)
    (finish-output stream)))

(defun handle-request (stream)
  "Read one request from STREAM, answer it, and close the connection."
  (multiple-value-bind (header-text complete) (read-until-blank-line stream)
    (if (not complete)
        (write-response stream 422 "{\"error\":\"bad_request\"}")
        (let ((headers (header-pairs header-text)))
          (let ((body (read-body stream headers)))
            (if (eq body :too-large)
                (write-response stream 413 "{\"error\":\"body_too_large\"}")
                (handler-case
                    (let ((request (parse-request header-text body)))
                      (let ((reply (textstat.contract:route
                                    (request-method request)
                                    (request-path request)
                                    (request-query request)
                                    (request-body request))))
                        (write-response stream
                                        (textstat.contract:reply-status reply)
                                        (textstat.contract:reply-body reply))))
                  (error ()
                    (write-response stream 422 "{\"error\":\"invalid_json\"}")))))))))

(defun handle-client (client)
  "Serve one accepted socket. Any error closes the connection without killing the server."
  (unwind-protect
       (let ((stream (sb-bsd-sockets:socket-make-stream
                      client :input t :output t :element-type '(unsigned-byte 8))))
         (handler-case (handle-request stream)
           (error (condition)
             (format *error-output* "connection failed: ~A~%" condition)
             (finish-output *error-output*)))
         (close stream))
    (sb-bsd-sockets:socket-close client)))

(defun serve (host port)
  "Bind HOST:PORT and answer requests until the process is killed.
   Each connection gets its own thread so a slow client cannot stall the accept loop."
  (let* ((address (sb-bsd-sockets:host-ent-address
                   (sb-bsd-sockets:get-host-by-name host)))
         (socket (make-instance 'sb-bsd-sockets:inet-socket :type :stream :protocol :tcp)))
    (setf (sb-bsd-sockets:sockopt-reuse-address socket) t)
    (sb-bsd-sockets:socket-bind socket address port)
    (sb-bsd-sockets:socket-listen socket 16)
    (format t "listening on http://~A:~D~%" host port)
    (finish-output)
    (loop
      (let ((client (sb-bsd-sockets:socket-accept socket)))
        (sb-thread:make-thread (lambda () (handle-client client)))))))

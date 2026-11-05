;;; Counting bytes. No port, no file, no printing: bytes in, a record out.
(define-module (textstat counts)
  #:use-module (rnrs bytevectors)
  #:use-module (srfi srfi-9)
  #:export (make-counts counts? counts-lines counts-words counts-bytes
            counts-of-bytevector counts->json json-quote))

(define-record-type <counts>
  (make-counts lines words bytes)
  counts?
  (lines counts-lines)
  (words counts-words)
  (bytes counts-bytes))

;;; space, tab, newline, carriage return, vertical tab, form feed
(define (byte-space? byte)
  (or (= byte 32) (= byte 9) (= byte 10) (= byte 13) (= byte 11) (= byte 12)))

(define (counts-of-bytevector bv)
  (let ((size (bytevector-length bv)))
    (let loop ((i 0) (lines 0) (words 0) (in-word? #f))
      (if (= i size)
          (make-counts lines words size)
          (let ((byte (bytevector-u8-ref bv i)))
            (cond
             ((= byte 10) (loop (+ i 1) (+ lines 1) words #f))
             ((byte-space? byte) (loop (+ i 1) lines words #f))
             (in-word? (loop (+ i 1) lines words #t))
             (else (loop (+ i 1) lines (+ words 1) #t))))))))

;;; JSON escaping over the string as it will be written: only the characters
;;; JSON forces us to escape are touched, everything else keeps its encoding.
(define (json-quote text)
  (let ((out (open-output-string)))
    (string-for-each
     (lambda (character)
       (let ((code (char->integer character)))
         (cond
          ((char=? character #\") (display "\\\"" out))
          ((char=? character #\\) (display "\\\\" out))
          ((char=? character #\newline) (display "\\n" out))
          ((char=? character #\return) (display "\\r" out))
          ((char=? character #\tab) (display "\\t" out))
          ((< code 32)
           (display "\\u" out)
           (display (string-pad (number->string code 16) 4 #\0) out))
          (else (display character out)))))
     text)
    (get-output-string out)))

(define (counts->json text counts)
  (string-append
   "{\"text\":\"" (json-quote text) "\""
   ",\"lines\":" (number->string (counts-lines counts))
   ",\"words\":" (number->string (counts-words counts))
   ",\"bytes\":" (number->string (counts-bytes counts))
   "}"))

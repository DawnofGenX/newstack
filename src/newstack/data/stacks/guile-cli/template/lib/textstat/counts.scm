;;; Counting bytes. No port, no file, no printing: a bytevector in, a record out.
(define-module (textstat counts)
  #:use-module (rnrs bytevectors)
  #:use-module (srfi srfi-9)
  #:export (make-counts counts? counts-lines counts-words counts-bytes
            counts-of-bytevector counts-add counts-columns
            byte-space? figure-width))

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
             ((= byte 10)
              (loop (+ i 1) (+ lines 1) words #f))
             ((byte-space? byte)
              (loop (+ i 1) lines words #f))
             (in-word?
              (loop (+ i 1) lines words #t))
             (else
              (loop (+ i 1) lines (+ words 1) #t))))))))

(define (counts-add left right)
  (make-counts (+ (counts-lines left) (counts-lines right))
               (+ (counts-words left) (counts-words right))
               (+ (counts-bytes left) (counts-bytes right))))

;;; the figures in the order wc prints them, whichever flags asked for them
(define (counts-columns figures tally)
  (let loop ((figures figures) (acc '()))
    (if (null? figures)
        (reverse acc)
        (loop (cdr figures)
              (cons (cond ((eq? (car figures) 'lines) (counts-lines tally))
                          ((eq? (car figures) 'words) (counts-words tally))
                          (else (counts-bytes tally)))
                    acc)))))

(define (figure-width value)
  (string-length (number->string value)))

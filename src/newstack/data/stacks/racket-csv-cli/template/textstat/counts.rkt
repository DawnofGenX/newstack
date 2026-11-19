#lang racket/base

;; Byte-level counting: the numbers `wc -l -w -c` prints, for the same bytes.
;; Everything here is pure — no ports, no files, no arguments.

(provide (struct-out counts)
         counts-of-bytes
         counts-add
         counts-columns)

(struct counts (lines words bytes) #:transparent)

;; The bytes `wc` treats as word separators: space, tab, newline, carriage
;; return, vertical tab, form feed.
(define (space-byte? byte)
  (or (= byte 32) (= byte 9) (= byte 10) (= byte 13) (= byte 11) (= byte 12)))

(define (counts-of-bytes data)
  (define size (bytes-length data))
  (let loop ([index 0] [lines 0] [words 0] [in-word? #f])
    (if (= index size)
        (counts lines words size)
        (let ([byte (bytes-ref data index)])
          (cond
            [(= byte 10)
             (loop (add1 index) (add1 lines) words #f)]
            [(space-byte? byte)
             (loop (add1 index) lines words #f)]
            [in-word?
             (loop (add1 index) lines words #t)]
            [else
             (loop (add1 index) lines (add1 words) #t)])))))

(define (counts-add left right)
  (counts (+ (counts-lines left) (counts-lines right))
          (+ (counts-words left) (counts-words right))
          (+ (counts-bytes left) (counts-bytes right))))

;; The figures a row shows, in the order wc prints them.
(define (counts-columns figures c)
  (append (if (memq 'lines figures) (list (counts-lines c)) '())
          (if (memq 'words figures) (list (counts-words c)) '())
          (if (memq 'bytes figures) (list (counts-bytes c)) '())))

#lang racket/base


(require json)
;; Counting rules plus the JSON they turn into. No socket, no request object.
(provide (struct-out counts)
         count-text
         counts->jsexpr
         json-string)

(struct counts (lines words bytes) #:transparent)

(define (count-text text)
  (define characters (string->list text))
  (define-values (lines words _in-word?)
    (for/fold ([lines 0] [words 0] [in-word? #f]) ([character characters])
      (cond
        [(char=? character #\newline) (values (add1 lines) words #f)]
        [(char-whitespace? character) (values lines words #f)]
        [in-word? (values lines words #t)]
        [else (values lines (add1 words) #t)])))
  (counts lines words (bytes-length (string->bytes/utf-8 text))))

(define (counts->jsexpr counts)
  (hasheq 'lines (counts-lines counts)
          'words (counts-words counts)
          'bytes (counts-bytes counts)))

(define (json-string value)
  (define out (open-output-string))
  (write-json value out)
  (get-output-string out))

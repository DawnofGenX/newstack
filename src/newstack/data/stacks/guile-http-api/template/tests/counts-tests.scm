;;; The counting rules, checked without a socket.
(define-module (counts-tests)
  #:use-module (rnrs bytevectors)
  #:use-module (harness)
  #:use-module (textstat counts)
  #:export (run-suite))

(define (counts-of text)
  (counts-of-bytevector (string->utf8 text)))

(define (run-suite)
  (check-equal "plain text" (counts-of "hello world\n") (make-counts 1 2 12))
  (check-equal "empty text" (counts-of "") (make-counts 0 0 0))
  (check-equal "blank lines" (counts-of "\n\nx\n") (make-counts 3 1 4))
  (check-equal "no newline" (counts-of "abc") (make-counts 0 1 3))
  (check-equal "only spaces" (counts-of "  \t ") (make-counts 0 0 4))
  (check-equal "utf8 bytes" (counts-of "héllo wörld\n") (make-counts 1 2 14))
  (check-equal "emoji is four bytes" (counts-of "🙂\n") (make-counts 1 1 5))
  (check-text "json quotes the text"
              (counts->json "a\"b" (make-counts 0 1 3))
              "{\"text\":\"a\\\"b\",\"lines\":0,\"words\":1,\"bytes\":3}")
  (check-text "json escapes a newline"
              (counts->json "a\nb" (make-counts 1 2 3))
              "{\"text\":\"a\\nb\",\"lines\":1,\"words\":2,\"bytes\":3}")
  (check-text "json escapes a tab"
              (counts->json "a\tb" (make-counts 0 2 3))
              "{\"text\":\"a\\tb\",\"lines\":0,\"words\":2,\"bytes\":3}"))

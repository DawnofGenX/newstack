#lang racket/base

;; The whole contract, exercised without a socket: counting rules first,
;; then one case per branch of the route table.
(require rackunit
         rackunit/text-ui
         json
         "../src/counts.rkt"
         "../src/contract.rkt")

(define (body->json outcome)
  (string->jsexpr (reply-body outcome)))

(define (status-of method path query body)
  (reply-status (route method path query body)))

(define counts-tests
  (test-suite
   "counting"
   (test-case "hello world"
     (check-equal? (count-text "hello world\n") (counts 1 2 12)))
   (test-case "empty input counts nothing"
     (check-equal? (count-text "") (counts 0 0 0)))
   (test-case "blank lines are lines"
     (check-equal? (count-text "\n\nx\n") (counts 3 1 4)))
   (test-case "whitespace without a word"
     (check-equal? (count-text "  \t ") (counts 0 0 4)))
   (test-case "a word without a trailing newline"
     (check-equal? (count-text "abc") (counts 0 1 3)))
   (test-case "utf-8 bytes are bytes, not characters"
     (check-equal? (count-text "héllo wörld\n") (counts 1 2 14)))
   (test-case "multi-byte characters"
     (check-equal? (count-text "🙂\n") (counts 1 1 5)))))

(define contract-tests
  (test-suite
   "contract"
   (test-case "health"
     (check-equal? (body->json (route "GET" "/health" "" "")) (hasheq 'status "ok")))
   (test-case "GET /stats counts the query"
     (check-equal? (body->json (route "GET" "/stats" "text=hello%20world%0A" ""))
                   (hasheq 'text "hello world\n" 'lines 1 'words 2 'bytes 12)))
   (test-case "GET /stats decodes plus as space"
     (check-equal? (body->json (route "GET" "/stats" "text=a+b" ""))
                   (hasheq 'text "a b" 'lines 0 'words 2 'bytes 3)))
   (test-case "GET /stats decodes an encoded ampersand"
     (check-equal? (body->json (route "GET" "/stats" "text=a%26b" ""))
                   (hasheq 'text "a&b" 'lines 0 'words 1 'bytes 3)))
   (test-case "GET /stats without text is 422"
     (check-equal? (status-of "GET" "/stats" "" "") 422)
     (check-equal? (body->json (route "GET" "/stats" "" "")) (hasheq 'error "missing_text")))
   (test-case "POST /stats counts the body"
     (check-equal? (body->json (route "POST" "/stats" "" "{\"text\":\"a b\nc\n\"}"))
                   (hasheq 'text "a b\nc\n" 'lines 2 'words 3 'bytes 6)))
   (test-case "POST /stats with no text is 422"
     (check-equal? (status-of "POST" "/stats" "" "{}") 422))
   (test-case "POST /stats with a non-string text is 422"
     (check-equal? (body->json (route "POST" "/stats" "" "{\"text\":42}"))
                   (hasheq 'error "missing_text")))
   (test-case "POST /stats with a broken body is 422"
     (check-equal? (body->json (route "POST" "/stats" "" "nope"))
                   (hasheq 'error "invalid_json")))
   (test-case "POST /stats with a json scalar is not an object"
     (check-equal? (status-of "POST" "/stats" "" "\"text\"") 422))
   (test-case "unknown route is a json 404 with the method and path"
     (check-equal? (body->json (route "GET" "/nope" "" ""))
                   (hasheq 'error "not_found" 'detail "no route for GET /nope")))
   (test-case "a known path with another method is 405"
     (check-equal? (status-of "DELETE" "/health" "" "") 405)
     (check-equal? (status-of "PUT" "/stats" "" "") 405))))

(define suite
  (test-suite
   "textstat"
   counts-tests
   contract-tests))

(exit (if (zero? (run-tests suite)) 0 1))

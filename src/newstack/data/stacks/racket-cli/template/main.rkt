#lang racket/base

;; The only module that touches the real process: files, standard input,
;; standard output and the exit status.  Everything it does is delegated to
;; textstat/runner.rkt; what is left here is the four funs it is handed.

(require racket/file
         racket/port
         "textstat/runner.rkt")

(provide main
         process-io
         read-stdin-bytes)

;; Bytes, not characters: `wc` counts bytes and so do we, even when the text is
;; UTF-8 or holds control characters.
(define (read-stdin-bytes)
  (let ([out (open-output-bytes)])
    (copy-port (current-input-port) out)
    (get-output-bytes out)))

(define (process-io)
  (io (lambda (path)
        (and (file-exists? path)
             (with-handlers ([exn:fail? (lambda (_) #f)])
               (file->bytes path))))
      read-stdin-bytes
      (lambda (text) (display text) (flush-output))
      (lambda (text) (eprintf "~a" text))))

(define (main)
  (exit (run (vector->list (current-command-line-arguments)) (process-io))))

(module+ main
  (main))

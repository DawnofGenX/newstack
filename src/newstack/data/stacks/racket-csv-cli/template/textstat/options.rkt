#lang racket/base

;; The argv parser: turns a list of strings into what to do, with no side
;; effects and no knowledge of files that exist.

(provide (struct-out options)
         tool-version
         parse-args
         usage)

(struct options (status figures files message) #:transparent)

(define tool-version "0.1.0")

(define (usage program)
  (string-append
   "usage: " program " [-l] [-w] [-c] [FILE ...]\n"
   "\n"
   "Count lines, words and bytes in each FILE, or in standard input.\n"
   "\n"
   "  -l, --lines    print the line count\n"
   "  -w, --words    print the word count\n"
   "  -c, --bytes    print the byte count\n"
   "  -h, --help     show this message\n"
   "  -V, --version  show the version\n"
   "\n"
   "With no figure flags, all three are printed.  A FILE of - means standard\n"
   "input; with no FILE at all, standard input is counted.\n"))

;; figures is a list of 'lines 'words 'bytes in the order the flags appeared;
;; duplicates collapse, and an empty list means "all three".
(define (add-figure figures figure)
  (if (memq figure figures) figures (cons figure figures)))
(define (parse-args arguments)
  (let loop ([rest arguments]
             [figures '()]
             [files '()]
             [only? #f])
    (define (done status message)
      (options status (if (null? figures) '(lines words bytes) (reverse figures))
               (reverse files) message))
    (cond
      [(null? rest) (done 'ok #f)]
      [only? (loop (cdr rest) figures (cons (car rest) files) #t)]
      [(equal? (car rest) "--") (loop (cdr rest) figures files #t)]
      [(member (car rest) '("-h" "--help"))
       (options 'help (if (null? figures) '(lines words bytes) (reverse figures))
                (reverse files) #f)]
      [(member (car rest) '("-V" "--version"))
       (options 'version (if (null? figures) '(lines words bytes) (reverse figures))
                (reverse files) #f)]
      [(member (car rest) '("-l" "--lines"))
       (loop (cdr rest) (add-figure figures 'lines) files #f)]
      [(member (car rest) '("-w" "--words"))
       (loop (cdr rest) (add-figure figures 'words) files #f)]
      [(member (car rest) '("-c" "--bytes"))
       (loop (cdr rest) (add-figure figures 'bytes) files #f)]
      [(and (> (string-length (car rest)) 2)
            (equal? (substring (car rest) 0 2) "--"))
       (options 'error (if (null? figures) '(lines words bytes) (reverse figures))
                (reverse files)
                (string-append "unknown option: " (car rest)))]
      [(and (> (string-length (car rest)) 1)
            (equal? (substring (car rest) 0 1) "-")
            (not (equal? (car rest) "-")))
       ;; a cluster of short flags, like -lw
       (let ([letters (string->list (substring (car rest) 1))])
         (let cluster ([letters letters] [figures figures])
           (cond
             [(null? letters) (loop (cdr rest) figures files #f)]
             [(memv (car letters) '(#\l #\w #\c))
              (cluster (cdr letters)
                       (add-figure figures
                                   (case (car letters)
                                     [(#\l) 'lines]
                                     [(#\w) 'words]
                                     [(#\c) 'bytes])))]
             [else
              (options 'error (if (null? figures) '(lines words bytes)
                                  (reverse figures))
                       (reverse files)
                       (string-append "unknown option: -" (string (car letters))))])))]
      [else (loop (cdr rest) figures (cons (car rest) files) #f)])))

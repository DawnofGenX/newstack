;;; argv in, a decision out. This module never opens a file or prints.
(define-module (textstat options)
  #:use-module (srfi srfi-9)
  #:export (make-parsed parsed? parsed-status parsed-message parsed-figures
            parsed-files parsed-show?
            parse-args usage tool-version)
  #:export-syntax ())

(define-record-type <parsed>
  (make-parsed status message figures files)
  parsed?
  (status parsed-status)
  (message parsed-message)
  (figures parsed-figures)
  (files parsed-files))

(define tool-version "0.1.0")

(define (parsed-show? parsed figure)
  (memq figure (parsed-figures parsed)))

(define (usage program)
  (string-append
   "Usage: " program " [OPTION]... [FILE]...\n"
   "Print newline, word, and byte counts for each FILE.\n"
   "\n"
   "  -l, --lines    print the newline count\n"
   "  -w, --words    print the word count\n"
   "  -c, --bytes    print the byte count\n"
   "  -h, --help     show this help and exit\n"
   "  -V, --version  show the version and exit\n"
   "\n"
   "With no FILE, or when FILE is -, read standard input.\n"))

;;; The walk keeps five things: the status, the message that explains a
;;; refusal, the figures asked for, the files collected so far, and whether
;;; "--" has turned every later word into a file.
(define (parse-args args)
  (define (finish status message figures files)
    (make-parsed status message
                 (if (or (null? figures) (not (eq? status 'ok)))
                     '(lines words bytes)
                     (canonical figures))
                 (reverse files)))
  (define (add-figure figures figure)
    (if (memq figure figures) figures (cons figure figures)))
  (let walk ((rest args) (status 'ok) (message "") (figures '()) (files '())
             (only? #f))
    (if (null? rest)
        (finish status message figures files)
        (let ((word (car rest)))
          (cond
           ((not (eq? status 'ok))
            (walk (cdr rest) status message figures files only?))
           ((and (not only?) (string=? word "--"))
            (walk (cdr rest) status message figures files #t))
           ((and (not only?) (string=? word "-"))
            (walk (cdr rest) status message figures (cons word files) only?))
           ((and (not only?) (> (string-length word) 1)
                 (char=? (string-ref word 0) #\-)
                 (char=? (string-ref word 1) #\-))
            (let ((name (substring word 2 (string-length word))))
              (cond
               ((string=? name "lines")
                (walk (cdr rest) status message (add-figure figures 'lines) files only?))
               ((string=? name "words")
                (walk (cdr rest) status message (add-figure figures 'words) files only?))
               ((string=? name "bytes")
                (walk (cdr rest) status message (add-figure figures 'bytes) files only?))
               ((string=? name "help") (walk (cdr rest) 'help "" figures files only?))
               ((string=? name "version") (walk (cdr rest) 'version "" figures files only?))
               (else
                (walk (cdr rest) 'usage-error
                      (string-append "unknown option: " word) figures files only?)))))
           ((and (not only?) (> (string-length word) 1)
                 (char=? (string-ref word 0) #\-))
            (let cluster ((i 1) (status status) (figures figures) (message ""))
              (if (>= i (string-length word))
                  (walk (cdr rest) status message figures files only?)
                  (let ((letter (string-ref word i)))
                    (cond
                     ((char=? letter #\l)
                      (cluster (+ i 1) status (add-figure figures 'lines) message))
                     ((char=? letter #\w)
                      (cluster (+ i 1) status (add-figure figures 'words) message))
                     ((char=? letter #\c)
                      (cluster (+ i 1) status (add-figure figures 'bytes) message))
                     ((char=? letter #\h) (walk (cdr rest) 'help "" figures files only?))
                     ((char=? letter #\V) (walk (cdr rest) 'version "" figures files only?))
                     (else
                      (walk (cdr rest) 'usage-error
                            (string-append "unknown option: -" (string letter))
                            figures files only?)))))))
           (else
            (walk (cdr rest) status message figures (cons word files) only?)))))))

;;; wc prints the figures in this order however they were asked for
(define (canonical figures)
  (if (null? figures)
      '()
      (let loop ((order '(lines words bytes)) (acc '()))
        (if (null? order)
            (reverse acc)
            (loop (cdr order)
                  (if (memq (car order) figures) (cons (car order) acc) acc))))))

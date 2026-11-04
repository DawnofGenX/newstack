\ Unit checks for the counting core, the argv parser and the row builder.
\ The CLI itself is exercised by tests/run_tests.sh, which diffs it against
\ the host wc.

require ../lib/counts.fs
require ../lib/options.fs
require ../lib/runner.fs
require harness.fs

: counts-suite ( -- )
  s\" alpha beta" counts-of 0 2 10 s" plain lines" s" plain words" s" plain bytes" check-fig
  s\" " counts-of 0 0 0 s" empty lines" s" empty words" s" empty bytes" check-fig
  s\" one\n" counts-of 1 1 4 s" trailing lines" s" trailing words" s" trailing bytes" check-fig
  s\" one" counts-of 0 1 3 s" no-newline lines" s" no-newline words" s" no-newline bytes" check-fig
  s\" alpha beta\ngamma delta\n" counts-of 2 4 23 s" two-line lines" s" two-line words" s" two-line bytes" check-fig
  s\" \t \n\r\v\f" counts-of 1 0 6 s" separator lines" s" separator words" s" separator bytes" check-fig
  s\" a\tb\vc\fd e\n" counts-of 1 5 10 s" control lines" s" control words" s" control bytes" check-fig
  s\" héllo wörld\n" counts-of 1 2 14 s" multibyte lines" s" multibyte words" s" multibyte bytes" check-fig
  s\" one two three four five six seven eight nine ten eleven" counts-of 0 11 55 s" many lines" s" many words" s" many bytes" check-fig
  totals-reset s\" a b" counts-of totals-add s\" c" counts-of totals-add
  TOTAL-LINES @ 0 = s" total lines" check
  TOTAL-WORDS @ 3 = s" total words" check
  TOTAL-BYTES @ 4 = s" total bytes" check ;

: options-suite ( -- )
  s" --lines f1" 2 set-args parse-args
  OPT-STATUS @ 0= s" --lines status" check
  OPT-L @ 1 = s" --lines on" check
  OPT-W @ 0= s" --lines words off" check
  OPT-NFILES @ 1 = s" --lines one file" check
  0 file-len 2 = s" --lines file length" check
  0 file-addr 0 file-len s" f1" compare 0= s" --lines file name" check

  s" -lw f1" 2 set-args parse-args
  OPT-L @ 1 = s" cluster lines" check
  OPT-W @ 1 = s" cluster words" check
  OPT-C @ 0= s" cluster bytes off" check
  OPT-ANY @ 1 = s" cluster any figure" check

  s" f1" 1 set-args parse-args
  OPT-L @ 1 = s" default lines" check
  OPT-W @ 1 = s" default words" check
  OPT-C @ 1 = s" default bytes" check

  s" --bogus" 1 set-args parse-args
  OPT-STATUS @ 3 = s" long option status" check
  MSGBUF MSGLEN @ s" unknown option: --bogus" compare 0= s" long option message" check

  s" -x" 1 set-args parse-args
  OPT-STATUS @ 3 = s" short option status" check
  MSGBUF MSGLEN @ s" unknown option: -x" compare 0= s" short option message" check

  s" --help" 1 set-args parse-args OPT-STATUS @ 1 = s" long help" check
  s" -h" 1 set-args parse-args OPT-STATUS @ 1 = s" short help" check
  s" --version" 1 set-args parse-args OPT-STATUS @ 2 = s" long version" check
  s" -V" 1 set-args parse-args OPT-STATUS @ 2 = s" short version" check

  s" --lines --words f1" 3 set-args parse-args
  OPT-ANY @ 1 = s" two long flags any" check
  OPT-C @ 0= s" two long flags bytes off" check

  s" -- --lines" 2 set-args parse-args
  OPT-STATUS @ 0= s" terminator status" check
  OPT-NFILES @ 1 = s" terminator one file" check
  OPT-L @ 1 = s" terminator default lines" check

  s" - f1" 2 set-args parse-args OPT-NFILES @ 2 = s" dash is a file" check
  s" --bytes" 1 set-args parse-args OPT-C @ 1 = s" --bytes on" check ;

: lbl ( -- addr u ) s" README" ;

: runner-suite ( -- )
  0 OPT-L ! 1 OPT-W ! 0 OPT-C !
  s\" alpha beta\ngamma\n" counts-of
  0 ROW-COUNT ! row-reset
  lbl row-push
  ROW-COUNT @ 1 = s" one row pushed" check
  0 cells ROW-LABEL-LEN + @ 6 = s" row label length" check
  0 cells ROW-LABEL-PTR + @ 0 cells ROW-LABEL-LEN + @ s" README" compare 0= s" row label text" check
  0 cells ROW-W + @ 3 = s" row words stored" check
  program-name s" {{ npm_name }}" compare 0= s" program name" check
  tool-version s" 0.1.0" compare 0= s" tool version" check ;

har-reset
counts-suite
options-suite
runner-suite
har-report (bye)

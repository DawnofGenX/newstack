\ Everything the CLI decides: reading, padding, totals and messages.

variable BUF-ADDR
variable BUF-LEN
variable BUF-CAP
variable CUR-FILE
variable WIDTH
variable PIPE-COUNT
variable FAILED-COUNT
variable ROW-COUNT
variable EXIT-CODE

create ROW-L 32 cells allot
create ROW-W 32 cells allot
create ROW-B 32 cells allot
create ROW-LABEL-PTR 32 cells allot
create ROW-LABEL-LEN 32 cells allot

create ROWBUF 1024 allot
variable ROWLEN

create NUMBUF 32 allot
variable NUMLEN
variable CELLS-PRINTED

: program-name ( -- addr u ) s" {{ npm_name }}" ;
: tool-version ( -- addr u ) s" 0.1.0" ;

: buf-init ( -- )
  8192 allocate throw BUF-ADDR ! 0 BUF-LEN ! 8192 BUF-CAP ! ;

: buf-free ( -- ) BUF-ADDR @ free throw ;

: buf-grow ( -- )
  BUF-CAP @ 2* dup BUF-CAP !
  BUF-ADDR @ swap resize throw BUF-ADDR ! ;

\ Reads one chunk into the arena and returns how many bytes arrived.
: read-chunk { fileid -- u }
  begin BUF-LEN @ BUF-CAP @ >= while buf-grow repeat
  BUF-ADDR @ BUF-LEN @ +
  BUF-CAP @ BUF-LEN @ -
  fileid read-file throw ;

: slurp-path { addr u -- ok }
  0 BUF-LEN !
  addr u r/o open-file if drop false exit then CUR-FILE !
  begin CUR-FILE @ read-chunk dup while BUF-LEN +! repeat drop
  CUR-FILE @ close-file throw true ;

: slurp-stdin ( -- )
  0 BUF-LEN !
  begin stdin read-chunk dup while BUF-LEN +! repeat drop ;

: err-type { addr u -- } addr u stderr write-file throw ;

: row-reset ( -- ) 0 ROWLEN ! 0 CELLS-PRINTED ! ;
: row-append { addr u -- } addr ROWBUF ROWLEN @ + u cmove u ROWLEN +! ;
create SPACEBUF 1 allot
: row-space ( -- ) bl SPACEBUF c! SPACEBUF 1 row-append ;
: row-type ( -- ) ROWBUF ROWLEN @ type ;

: num>buf ( n -- )
  0 <# #s #> NUMBUF swap dup NUMLEN ! cmove ;

: row-cell { n width -- }
  CELLS-PRINTED @ 0> if row-space then
  n num>buf
  width NUMLEN @ - 0 max 0 ?do row-space loop
  NUMBUF NUMLEN @ row-append
  1 CELLS-PRINTED +! ;

: figures-count ( -- u ) OPT-L @ OPT-W @ + OPT-C @ + ;

\ The width wc would use: one figure over one row keeps its own width, a pipe
\ pads to seven columns, otherwise the digit count of the total byte count.
: column-width ( -- u )
  figures-count 1 = ROW-COUNT @ 1 <= and if
    ROW-COUNT @ 0= if 1 exit then
    OPT-L @ if 0 cells ROW-L + @ num>buf NUMLEN @ exit then
    OPT-W @ if 0 cells ROW-W + @ num>buf NUMLEN @ exit then
    0 cells ROW-B + @ num>buf NUMLEN @ exit
  then
  PIPE-COUNT @ 0> if 7 exit then
  TOTAL-BYTES @ num>buf NUMLEN @ ;

: row-push { label-addr label-len -- }
  ROW-COUNT @ cells ROW-L + TS-LINES @ swap !
  ROW-COUNT @ cells ROW-W + TS-WORDS @ swap !
  ROW-COUNT @ cells ROW-B + TS-BYTES @ swap !
  label-addr ROW-COUNT @ cells ROW-LABEL-PTR + !
  label-len ROW-COUNT @ cells ROW-LABEL-LEN + !
  1 ROW-COUNT +! ;

: row-print { row -- }
  row-reset
  OPT-L @ if row cells ROW-L + @ WIDTH @ row-cell then
  OPT-W @ if row cells ROW-W + @ WIDTH @ row-cell then
  OPT-C @ if row cells ROW-B + @ WIDTH @ row-cell then
  row cells ROW-LABEL-LEN + @ 0> if
    row-space
    row cells ROW-LABEL-PTR + @ row cells ROW-LABEL-LEN + @ row-append
  then
  row-type cr ;

: total-print ( -- )
  row-reset
  OPT-L @ if TOTAL-LINES @ WIDTH @ row-cell then
  OPT-W @ if TOTAL-WORDS @ WIDTH @ row-cell then
  OPT-C @ if TOTAL-BYTES @ WIDTH @ row-cell then
  s"  total" row-append
  row-type cr ;

: read-one { i -- }
  i file-len 1 = i file-addr c@ [char] - = and
  if
    1 PIPE-COUNT +!
    slurp-stdin
    BUF-ADDR @ BUF-LEN @ counts-of
    i file-addr i file-len row-push
    totals-add
  else
    i file-addr i file-len slurp-path
    if
      BUF-ADDR @ BUF-LEN @ counts-of
      i file-addr i file-len row-push
      totals-add
    else
      1 FAILED-COUNT +!
      s" error: cannot open '" err-type
      i file-addr i file-len err-type
      s\" '\n" err-type
    then
  then ;

: report ( -- )
  buf-init
  0 PIPE-COUNT ! 0 FAILED-COUNT ! 0 ROW-COUNT ! 0 EXIT-CODE !
  totals-reset
  OPT-NFILES @ 0= if
    1 PIPE-COUNT +!
    slurp-stdin
    BUF-ADDR @ BUF-LEN @ counts-of
    totals-add
    s" " drop 0 row-push
  else
    0 begin dup OPT-NFILES @ < while dup read-one 1+ repeat drop
  then
  column-width WIDTH !
  ROW-COUNT @ 0 ?do i row-print loop
  OPT-NFILES @ 1 > if total-print then
  FAILED-COUNT @ 0> if 1 else 0 then EXIT-CODE !
  buf-free ;

: usage-print ( -- )
  s" Usage: " type program-name type s"  [OPTION]... [FILE]..." type cr
  cr
  s" Print newline, word, and byte counts for each FILE." type cr
  cr
  s"   -l, --lines    print the newline counts" type cr
  s"   -w, --words    print the word counts" type cr
  s"   -c, --bytes    print the byte counts" type cr
  s"   -h, --help     show this help and exit" type cr
  s"   -V, --version  show the version and exit" type cr
  cr
  s" With no FILE, or when FILE is -, read standard input." type cr ;

: refuse-print ( -- )
  program-name err-type
  s" : " err-type
  MSGBUF MSGLEN @ err-type
  s\" \n" err-type
  s" Try '" err-type
  program-name err-type
  s"  --help' for more information." err-type
  s\" \n" err-type ;

\ Runs the whole CLI and leaves the exit status.
: run ( -- code )
  parse-args
  OPT-STATUS @ 0= if report EXIT-CODE @ exit then
  OPT-STATUS @ 1 = if usage-print 0 exit then
  OPT-STATUS @ 2 = if tool-version type cr 0 exit then
  refuse-print 2 ;

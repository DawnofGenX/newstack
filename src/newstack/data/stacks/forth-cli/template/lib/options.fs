\ The argv parser. Arguments arrive as ( addr u ) pairs, so a name with a space
\ or a leading dash is just text here; nothing is ever handed to the OS.

create ARG-BUF 8192 allot
variable ARG-POS
create ARG-PTR 64 cells allot
create ARG-LENGTHS 64 cells allot
variable ARG-N

create FILE-PTR 64 cells allot
create FILE-LENGTHS 64 cells allot
variable OPT-NFILES

variable OPT-STATUS   \ 0 ok, 1 help, 2 version, 3 usage error
variable OPT-L
variable OPT-W
variable OPT-C
variable OPT-ANY
variable OPT-LITERAL

create MSGBUF 256 allot
variable MSGLEN

create CHARBUF 1 allot

: args-clear ( -- ) 0 ARG-POS ! 0 ARG-N ! ;

\ Copies one argument into the arena so a caller may reuse its buffer.
: args-push { addr u -- }
  ARG-BUF ARG-POS @ + >r
  r@ ARG-N @ cells ARG-PTR + !
  u ARG-N @ cells ARG-LENGTHS + !
  addr r> u cmove
  u ARG-POS +!  1 ARG-N +! ;

\ Takes every argument gforth was given, skipping the image and the script.
: args-from-command-line ( -- )
  args-clear
  begin next-arg dup while args-push repeat 2drop ;

: arg-addr ( i -- addr ) cells ARG-PTR + @ ;
: arg-len ( i -- u ) cells ARG-LENGTHS + @ ;

: arg= { i addr u -- }
  i arg-len u <> if false exit then
  i arg-addr i arg-len addr u compare 0= ;

: file-record ( i -- )
  dup arg-addr OPT-NFILES @ cells FILE-PTR + !
  dup arg-len OPT-NFILES @ cells FILE-LENGTHS + !
  OPT-NFILES @ 1+ OPT-NFILES ! drop ;

: file-addr ( i -- addr ) cells FILE-PTR + @ ;
: file-len ( i -- u ) cells FILE-LENGTHS + @ ;

: msg-reset ( -- ) 0 MSGLEN ! ;
: msg-append { addr u -- } addr MSGBUF MSGLEN @ + u cmove u MSGLEN +! ;
: msg-error ( -- ) 3 OPT-STATUS ! ;

: status-ok? ( -- flag ) OPT-STATUS @ 0= ;

: unknown-long ( i -- ) msg-reset s" unknown option: " msg-append dup arg-addr swap arg-len msg-append msg-error ;

variable CUR

: cluster ( -- )
  CUR @ arg-len 1 ?do
    CUR @ arg-addr i + c@
    dup [char] l = if drop 1 OPT-L ! 1 OPT-ANY ! else
    dup [char] w = if drop 1 OPT-W ! 1 OPT-ANY ! else
    dup [char] c = if drop 1 OPT-C ! 1 OPT-ANY ! else
    dup [char] h = if drop 1 OPT-STATUS ! leave else
    dup [char] V = if drop 2 OPT-STATUS ! leave else
        CHARBUF c!
        msg-reset s" unknown option: -" msg-append CHARBUF 1 msg-append msg-error
        leave
    then then then then then
  loop ;

: long-option ( -- )
  CUR @ s" --lines" arg= if 1 OPT-L ! 1 OPT-ANY ! exit then
  CUR @ s" --words" arg= if 1 OPT-W ! 1 OPT-ANY ! exit then
  CUR @ s" --bytes" arg= if 1 OPT-C ! 1 OPT-ANY ! exit then
  CUR @ s" --help" arg= if 1 OPT-STATUS ! exit then
  CUR @ s" --version" arg= if 2 OPT-STATUS ! exit then
  CUR @ unknown-long ;

: parse-one ( -- )
  CUR @ arg-len 0= if CUR @ file-record exit then
  OPT-LITERAL @ 0= if
    CUR @ s" --" arg= if 1 OPT-LITERAL ! exit then
    CUR @ s" -" arg= if CUR @ file-record exit then
    CUR @ arg-addr c@ [char] - = if
      CUR @ arg-addr 1+ c@ [char] - = if long-option else cluster then
      exit
    then
  then
  CUR @ file-record ;

: parse-args ( -- )
  0 OPT-STATUS ! 0 OPT-L ! 0 OPT-W ! 0 OPT-C ! 0 OPT-ANY ! 0 OPT-LITERAL ! 0 OPT-NFILES !
  0 CUR !
  begin CUR @ ARG-N @ < status-ok? and while
    parse-one
    CUR @ 1+ CUR !
  repeat
  OPT-ANY @ 0= if 1 OPT-L ! 1 OPT-W ! 1 OPT-C ! then ;

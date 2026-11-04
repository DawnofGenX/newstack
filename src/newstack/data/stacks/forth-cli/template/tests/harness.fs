\ A small test harness: it counts what passed and names what failed.

variable T-PASSED
variable T-FAILED

: har-reset ( -- ) 0 T-PASSED ! 0 T-FAILED ! ;
: har-pass ( -- ) 1 T-PASSED +! ;
: har-fail ( -- ) 1 T-FAILED +! ;

\ flag addr u -- ; prints "FAIL <name>" when the flag is false.
: check ( flag addr u -- )
  rot if har-pass 2drop else ." FAIL " type cr har-fail then ;

\ actual expected addr u --
: check-num ( actual expected addr u -- )
  rot = check ;

\ Splits a space-separated string into the argv list the parser walks.
: set-args { addr u n -- }
  n drop args-clear
  begin u 0> while
    addr u bl scan { p q }
    addr u q - args-push
    p 1+ to addr
    q 1- to u
  repeat ;

\ Checks the tally left by counts-of:
\ ( want-lines want-words want-bytes lines-name words-name bytes-name -- )
: check-fig { want-l want-w want-b la lu wa wu ba bu -- }
  TS-LINES @ want-l = la lu check
  TS-WORDS @ want-w = wa wu check
  TS-BYTES @ want-b = ba bu check ;

\ Sorts out the process status and prints the tally.
: har-report ( -- code )
  ." checks: " T-PASSED @ T-FAILED @ + 0 .r
  ." , passed: " T-PASSED @ 0 .r
  ." , failed: " T-FAILED @ 0 .r cr
  T-FAILED @ 0> if 1 else 0 then ;

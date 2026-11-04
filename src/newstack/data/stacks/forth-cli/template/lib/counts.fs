\ Counting over a memory block. Everything is a byte: the caller reads the whole
\ file into memory first, so the counts are exact whatever the file contains.

variable TS-LINES
variable TS-WORDS
variable TS-BYTES
variable TS-INWORD

variable TOTAL-LINES
variable TOTAL-WORDS
variable TOTAL-BYTES

: counts-reset ( -- )
  0 TS-LINES ! 0 TS-WORDS ! 0 TS-BYTES ! 0 TS-INWORD ! ;

: totals-reset ( -- )
  0 TOTAL-LINES ! 0 TOTAL-WORDS ! 0 TOTAL-BYTES ! ;

\ space, tab, newline, carriage return, vertical tab, form feed
: space-byte? ( c -- flag )
  dup 32 = over 9 = or over 10 = or over 13 = or over 11 = or swap 12 = or ;

\ Sets TS-LINES, TS-WORDS and TS-BYTES for the block at addr u.
: counts-of ( addr u -- )
  counts-reset
  dup TS-BYTES !
  over + swap ?do
    i c@ dup 10 = if 1 TS-LINES +! then
    space-byte? if
      0 TS-INWORD !
    else
      TS-INWORD @ 0= if 1 TS-WORDS +! then
      1 TS-INWORD !
    then
  loop ;

\ Folds the current tally into the running totals.
: totals-add ( -- )
  TS-LINES @ TOTAL-LINES +!
  TS-WORDS @ TOTAL-WORDS +!
  TS-BYTES @ TOTAL-BYTES +! ;

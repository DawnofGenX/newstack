      *> Unit driver: it calls the library units the way the runner does and
      *> prints one PASS/FAIL line per assertion, then a tally. The runner's
      *> own behaviour is exercised by tests/run_tests.sh against the binary.
       IDENTIFICATION DIVISION.
       PROGRAM-ID. TEXTSTAT-TESTS.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 WS-OP        PIC 9.
       01 WS-LEN       PIC 9(9) COMP-5.
       01 WS-BUF       PIC X(256).
       01 WS-COUNTS.
          05 WS-LINES  PIC 9(18) COMP-5.
          05 WS-WORDS  PIC 9(18) COMP-5.
          05 WS-BYTES  PIC 9(18) COMP-5.
       01 WS-ARGV      PIC X(8192).
       01 WS-ARGV-LEN  PIC 9(9) COMP-5.
       01 WS-PARSED.
          05 WS-STATUS PIC 9.
          05 WS-MESSAGE PIC X(120).
          05 WS-SHOW-L PIC 9.
          05 WS-SHOW-W PIC 9.
          05 WS-SHOW-C PIC 9.
          05 WS-NFILES PIC 9(4) COMP-5.
          05 WS-FILES.
             10 WS-FILE PIC X(256) OCCURS 64 TIMES.
       01 WS-WORDS-IN.
          05 WS-WORD-IN PIC X(64) OCCURS 8 TIMES.
       01 WS-NWORDS   PIC 9(4) COMP-5 VALUE 0.
       01 WS-PTR      PIC 9(9) COMP-5 VALUE 0.
       01 WS-ARG      PIC X(64).
       01 WS-ALEN     PIC 9(9) COMP-5 VALUE 0.
       01 WS-IDX      PIC 9(4) COMP-5 VALUE 1.
       01 WS-CHECKS   PIC 9(4) COMP-5 VALUE 0.
       01 WS-PASSED   PIC 9(4) COMP-5 VALUE 0.
       01 WS-FAILED   PIC 9(4) COMP-5 VALUE 0.
       01 WS-NAME     PIC X(56).
       01 WS-WANT     PIC 9(18) COMP-5 VALUE 0.
       01 WS-GOT      PIC 9(18) COMP-5 VALUE 0.
       01 WS-DETAIL   PIC X(80).
       01 WS-SPEC     PIC X(128).
       01 WS-EDIT-CHECKS PIC Z(4)9.
       01 WS-EDIT-PASSED PIC Z(4)9.
       01 WS-EDIT-FAILED PIC Z(4)9.
       PROCEDURE DIVISION.
       MAIN.
           PERFORM COUNT-PLAIN
           PERFORM COUNT-CONTROL
           PERFORM COUNT-EMPTY
           PERFORM COUNT-TAIL
           PERFORM OPTION-SHORT
           PERFORM OPTION-LONG
           PERFORM OPTION-DEFAULT
           PERFORM OPTION-CLUSTER
           PERFORM OPTION-TERMINATOR
           PERFORM OPTION-DASH
           PERFORM OPTION-HELP
           PERFORM OPTION-VERSION
           PERFORM OPTION-UNKNOWN
           PERFORM OPTION-MANY
           MOVE WS-CHECKS TO WS-EDIT-CHECKS
           MOVE WS-PASSED TO WS-EDIT-PASSED
           MOVE WS-FAILED TO WS-EDIT-FAILED
           DISPLAY "checks: " FUNCTION TRIM(WS-EDIT-CHECKS)
               ", passed: " FUNCTION TRIM(WS-EDIT-PASSED)
               ", failed: " FUNCTION TRIM(WS-EDIT-FAILED)
           MOVE WS-FAILED TO RETURN-CODE
           GOBACK.

       COUNT-PLAIN.
           MOVE 1 TO WS-OP
           MOVE 0 TO WS-LEN
           MOVE SPACES TO WS-BUF
           CALL "TEXTSTAT-COUNTS" USING WS-OP WS-LEN WS-BUF WS-COUNTS
           MOVE "alpha beta" TO WS-BUF
           MOVE X"0A" TO WS-BUF(11:1)
           MOVE "gamma" TO WS-BUF(12:5)
           MOVE X"0A" TO WS-BUF(17:1)
           MOVE 17 TO WS-LEN
           MOVE 2 TO WS-OP
           CALL "TEXTSTAT-COUNTS" USING WS-OP WS-LEN WS-BUF WS-COUNTS
           MOVE WS-LINES TO WS-GOT
           MOVE 2 TO WS-WANT
           MOVE "two lines in plain text" TO WS-NAME
           PERFORM CHECK-NUM
           MOVE WS-WORDS TO WS-GOT
           MOVE 3 TO WS-WANT
           MOVE "three words in plain text" TO WS-NAME
           PERFORM CHECK-NUM
           MOVE WS-BYTES TO WS-GOT
           MOVE 17 TO WS-WANT
           MOVE "seventeen bytes in plain text" TO WS-NAME
           PERFORM CHECK-NUM.

       COUNT-CONTROL.
           MOVE 1 TO WS-OP
           MOVE 0 TO WS-LEN
           MOVE SPACES TO WS-BUF
           CALL "TEXTSTAT-COUNTS" USING WS-OP WS-LEN WS-BUF WS-COUNTS
           MOVE "alpha" TO WS-BUF
           MOVE X"0B" TO WS-BUF(6:1)
           MOVE "beta" TO WS-BUF(7:4)
           MOVE X"0C" TO WS-BUF(11:1)
           MOVE 11 TO WS-LEN
           MOVE 2 TO WS-OP
           CALL "TEXTSTAT-COUNTS" USING WS-OP WS-LEN WS-BUF WS-COUNTS
           MOVE WS-WORDS TO WS-GOT
           MOVE 2 TO WS-WANT
           MOVE "vertical tab and form feed split words" TO WS-NAME
           PERFORM CHECK-NUM
           MOVE WS-BYTES TO WS-GOT
           MOVE 11 TO WS-WANT
           MOVE "control bytes still count as bytes" TO WS-NAME
           PERFORM CHECK-NUM
           MOVE WS-LINES TO WS-GOT
           MOVE 0 TO WS-WANT
           MOVE "no newline means no line yet" TO WS-NAME
           PERFORM CHECK-NUM.

       COUNT-EMPTY.
           MOVE 1 TO WS-OP
           MOVE 0 TO WS-LEN
           MOVE SPACES TO WS-BUF
           CALL "TEXTSTAT-COUNTS" USING WS-OP WS-LEN WS-BUF WS-COUNTS
           MOVE WS-LINES TO WS-GOT
           MOVE 0 TO WS-WANT
           MOVE "empty input has no lines" TO WS-NAME
           PERFORM CHECK-NUM
           MOVE WS-WORDS TO WS-GOT
           MOVE 0 TO WS-WANT
           MOVE "empty input has no words" TO WS-NAME
           PERFORM CHECK-NUM
           MOVE WS-BYTES TO WS-GOT
           MOVE 0 TO WS-WANT
           MOVE "empty input has no bytes" TO WS-NAME
           PERFORM CHECK-NUM.

       COUNT-TAIL.
           MOVE 1 TO WS-OP
           MOVE 0 TO WS-LEN
           MOVE SPACES TO WS-BUF
           CALL "TEXTSTAT-COUNTS" USING WS-OP WS-LEN WS-BUF WS-COUNTS
           MOVE "a b" TO WS-BUF
           MOVE 3 TO WS-LEN
           MOVE 2 TO WS-OP
           CALL "TEXTSTAT-COUNTS" USING WS-OP WS-LEN WS-BUF WS-COUNTS
           MOVE WS-LINES TO WS-GOT
           MOVE 0 TO WS-WANT
           MOVE "no trailing newline is no line yet" TO WS-NAME
           PERFORM CHECK-NUM
           MOVE WS-BYTES TO WS-GOT
           MOVE 3 TO WS-WANT
           MOVE "no trailing newline is three bytes" TO WS-NAME
           PERFORM CHECK-NUM.

       OPTION-SHORT.
           MOVE "-l x.txt" TO WS-SPEC
           PERFORM BUILD-ARGV
           PERFORM PARSE-ARGV
           MOVE WS-SHOW-L TO WS-GOT
           MOVE 1 TO WS-WANT
           MOVE "a lone -l shows lines" TO WS-NAME
           PERFORM CHECK-NUM
           MOVE WS-SHOW-W TO WS-GOT
           MOVE 0 TO WS-WANT
           MOVE "a lone -l leaves words off" TO WS-NAME
           PERFORM CHECK-NUM
           MOVE WS-NFILES TO WS-GOT
           MOVE 1 TO WS-WANT
           MOVE "the operand is collected" TO WS-NAME
           PERFORM CHECK-NUM.

       OPTION-LONG.
           MOVE "--words --bytes a.txt b.txt" TO WS-SPEC
           PERFORM BUILD-ARGV
           PERFORM PARSE-ARGV
           MOVE WS-SHOW-W TO WS-GOT
           MOVE 1 TO WS-WANT
           MOVE "long flags pick words" TO WS-NAME
           PERFORM CHECK-NUM
           MOVE WS-SHOW-C TO WS-GOT
           MOVE 1 TO WS-WANT
           MOVE "long flags pick bytes" TO WS-NAME
           PERFORM CHECK-NUM
           MOVE WS-SHOW-L TO WS-GOT
           MOVE 0 TO WS-WANT
           MOVE "long flags leave lines off" TO WS-NAME
           PERFORM CHECK-NUM
           MOVE WS-NFILES TO WS-GOT
           MOVE 2 TO WS-WANT
           MOVE "two operands are collected" TO WS-NAME
           PERFORM CHECK-NUM
           MOVE "first operand arrives intact" TO WS-NAME
           IF WS-FILE(1)(1:6) = "a.txt "
             PERFORM PASS
           ELSE
             PERFORM FAIL-FILE-1
           END-IF
           MOVE "second operand arrives intact" TO WS-NAME
           IF WS-FILE(2)(1:6) = "b.txt "
             PERFORM PASS
           ELSE
             PERFORM FAIL-FILE-2
           END-IF.

       OPTION-DEFAULT.
           MOVE "x.txt y.txt" TO WS-SPEC
           PERFORM BUILD-ARGV
           PERFORM PARSE-ARGV
           MOVE WS-SHOW-L TO WS-GOT
           MOVE 1 TO WS-WANT
           MOVE "no figure flag shows lines" TO WS-NAME
           PERFORM CHECK-NUM
           MOVE WS-SHOW-W TO WS-GOT
           MOVE 1 TO WS-WANT
           MOVE "no figure flag shows words" TO WS-NAME
           PERFORM CHECK-NUM
           MOVE WS-SHOW-C TO WS-GOT
           MOVE 1 TO WS-WANT
           MOVE "no figure flag shows bytes" TO WS-NAME
           PERFORM CHECK-NUM.

       OPTION-CLUSTER.
           MOVE "-lwc x.txt" TO WS-SPEC
           PERFORM BUILD-ARGV
           PERFORM PARSE-ARGV
           MOVE WS-SHOW-L TO WS-GOT
           MOVE 1 TO WS-WANT
           MOVE "a cluster turns lines on" TO WS-NAME
           PERFORM CHECK-NUM
           MOVE WS-SHOW-W TO WS-GOT
           MOVE 1 TO WS-WANT
           MOVE "a cluster turns words on" TO WS-NAME
           PERFORM CHECK-NUM
           MOVE WS-SHOW-C TO WS-GOT
           MOVE 1 TO WS-WANT
           MOVE "a cluster turns bytes on" TO WS-NAME
           PERFORM CHECK-NUM
           MOVE WS-NFILES TO WS-GOT
           MOVE 1 TO WS-WANT
           MOVE "a cluster leaves one operand" TO WS-NAME
           PERFORM CHECK-NUM.

       OPTION-TERMINATOR.
           MOVE "-l -- -w" TO WS-SPEC
           PERFORM BUILD-ARGV
           PERFORM PARSE-ARGV
           MOVE WS-NFILES TO WS-GOT
           MOVE 1 TO WS-WANT
           MOVE "after -- everything is a file" TO WS-NAME
           PERFORM CHECK-NUM
           MOVE WS-SHOW-L TO WS-GOT
           MOVE 1 TO WS-WANT
           MOVE "a flag before -- still counts" TO WS-NAME
           PERFORM CHECK-NUM
           MOVE WS-SHOW-W TO WS-GOT
           MOVE 0 TO WS-WANT
           MOVE "a flag after -- is only a name" TO WS-NAME
           PERFORM CHECK-NUM
           MOVE "the dash-w name survives" TO WS-NAME
           IF WS-FILE(1)(1:3) = "-w "
             PERFORM PASS
           ELSE
             MOVE "that file name did not survive" TO WS-DETAIL
             PERFORM FAIL
           END-IF.

       OPTION-DASH.
           MOVE "- x.txt" TO WS-SPEC
           PERFORM BUILD-ARGV
           PERFORM PARSE-ARGV
           MOVE WS-NFILES TO WS-GOT
           MOVE 2 TO WS-WANT
           MOVE "a lone dash is an operand" TO WS-NAME
           PERFORM CHECK-NUM
           MOVE "the dash operand keeps its name" TO WS-NAME
           IF WS-FILE(1)(1:2) = "- "
             PERFORM PASS
           ELSE
             MOVE "the dash operand was renamed" TO WS-DETAIL
             PERFORM FAIL
           END-IF.

       OPTION-HELP.
           MOVE "--help" TO WS-SPEC
           PERFORM BUILD-ARGV
           PERFORM PARSE-ARGV
           MOVE WS-STATUS TO WS-GOT
           MOVE 2 TO WS-WANT
           MOVE "help is its own status" TO WS-NAME
           PERFORM CHECK-NUM.

       OPTION-VERSION.
           MOVE "--version" TO WS-SPEC
           PERFORM BUILD-ARGV
           PERFORM PARSE-ARGV
           MOVE WS-STATUS TO WS-GOT
           MOVE 3 TO WS-WANT
           MOVE "version is its own status" TO WS-NAME
           PERFORM CHECK-NUM.

       OPTION-UNKNOWN.
           MOVE "--bogus" TO WS-SPEC
           PERFORM BUILD-ARGV
           PERFORM PARSE-ARGV
           MOVE WS-STATUS TO WS-GOT
           MOVE 4 TO WS-WANT
           MOVE "an unknown option is refused" TO WS-NAME
           PERFORM CHECK-NUM
           MOVE "the refusal names the option" TO WS-NAME
           IF WS-MESSAGE(1:22) = "unknown option: --bogu"
             PERFORM PASS
           ELSE
             MOVE SPACES TO WS-DETAIL
             STRING "got " WS-MESSAGE(1:30) DELIMITED BY SIZE
               INTO WS-DETAIL
             PERFORM FAIL
           END-IF.

       OPTION-MANY.
           MOVE "a.txt b.txt c.txt" TO WS-SPEC
           PERFORM BUILD-ARGV
           PERFORM PARSE-ARGV
           MOVE WS-NFILES TO WS-GOT
           MOVE 3 TO WS-WANT
           MOVE "three operands are collected" TO WS-NAME
           PERFORM CHECK-NUM.

      *> Turn WS-SPEC into the NUL-separated command line that
      *> /proc/self/cmdline gives the real entry point, program name first.
       BUILD-ARGV.
           MOVE SPACES TO WS-WORDS-IN
           MOVE 0 TO WS-NWORDS
           UNSTRING WS-SPEC DELIMITED BY ALL SPACE
             INTO WS-WORD-IN(1) WS-WORD-IN(2) WS-WORD-IN(3)
                  WS-WORD-IN(4) WS-WORD-IN(5) WS-WORD-IN(6)
                  WS-WORD-IN(7) WS-WORD-IN(8)
             TALLYING IN WS-NWORDS
           END-UNSTRING
           MOVE SPACES TO WS-ARGV
           MOVE LOW-VALUES TO WS-ARGV
           MOVE 0 TO WS-PTR
           MOVE "textstat-tests" TO WS-ARG
           PERFORM APPEND-ARG
           PERFORM VARYING WS-IDX FROM 1 BY 1 UNTIL WS-IDX > WS-NWORDS
             MOVE WS-WORD-IN(WS-IDX) TO WS-ARG
             PERFORM APPEND-ARG
           END-PERFORM
           MOVE WS-PTR TO WS-ARGV-LEN.

       APPEND-ARG.
           MOVE 0 TO WS-ALEN
           COMPUTE WS-ALEN = FUNCTION LENGTH(FUNCTION TRIM(WS-ARG))
           IF WS-ALEN > 0
             MOVE WS-ARG(1:WS-ALEN) TO WS-ARGV(WS-PTR + 1:WS-ALEN)
             ADD WS-ALEN TO WS-PTR
           END-IF
      *> the separator byte is already LOW-VALUE in WS-ARGV
           ADD 1 TO WS-PTR.

       PARSE-ARGV.
           CALL "TEXTSTAT-OPTIONS" USING WS-ARGV WS-ARGV-LEN WS-PARSED.

       CHECK-NUM.
           ADD 1 TO WS-CHECKS
           IF WS-WANT = WS-GOT
             ADD 1 TO WS-PASSED
             DISPLAY "PASS " WS-NAME
           ELSE
             ADD 1 TO WS-FAILED
             MOVE SPACES TO WS-DETAIL
             MOVE WS-WANT TO WS-EDIT-CHECKS
             MOVE WS-GOT TO WS-EDIT-PASSED
             STRING "want " FUNCTION TRIM(WS-EDIT-CHECKS)
               ", got " FUNCTION TRIM(WS-EDIT-PASSED)
               DELIMITED BY SIZE INTO WS-DETAIL
             DISPLAY "FAIL " WS-NAME " (" WS-DETAIL ")"
           END-IF.

       PASS.
           ADD 1 TO WS-CHECKS
           ADD 1 TO WS-PASSED
           DISPLAY "PASS " WS-NAME.

       FAIL.
           ADD 1 TO WS-CHECKS
           ADD 1 TO WS-FAILED
           DISPLAY "FAIL " WS-NAME " (" WS-DETAIL ")".

       FAIL-FILE-1.
           MOVE SPACES TO WS-DETAIL
           STRING "got " WS-FILE(1)(1:8) DELIMITED BY SIZE
             INTO WS-DETAIL
           PERFORM FAIL.

       FAIL-FILE-2.
           MOVE SPACES TO WS-DETAIL
           STRING "got " WS-FILE(2)(1:8) DELIMITED BY SIZE
             INTO WS-DETAIL
           PERFORM FAIL.

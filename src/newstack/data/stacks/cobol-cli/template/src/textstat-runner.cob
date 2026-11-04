       IDENTIFICATION DIVISION.
       PROGRAM-ID. TEXTSTAT-RUNNER.
      *> The only part that touches the outside world: it opens each operand,
      *> hands the bytes to TEXTSTAT-COUNTS, prints the rows and decides the
      *> exit code. The counting and the parsing live in their own programs.
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT F-DATA ASSIGN TO WS-PATH
               ORGANIZATION IS SEQUENTIAL
               FILE STATUS IS WS-FS.
       DATA DIVISION.
       FILE SECTION.
       FD F-DATA.
       01 F-BYTE PIC X(1).
       WORKING-STORAGE SECTION.
       01 WS-PATH      PIC X(256).
       01 WS-FS        PIC X(2).
       01 WS-EOF       PIC 9 VALUE 0.
       01 WS-BUF       PIC X(256).
       01 WS-BUFLEN    PIC 9(9) COMP-5 VALUE 0.
       01 WS-OP        PIC 9 VALUE 0.
       01 WS-COUNTS.
          05 WS-LINES  PIC 9(18) COMP-5.
          05 WS-WORDS  PIC 9(18) COMP-5.
          05 WS-BYTES  PIC 9(18) COMP-5.
       01 WS-ROWS.
          05 WS-ROW OCCURS 64 TIMES.
             10 WS-R-LINES PIC 9(18) COMP-5.
             10 WS-R-WORDS PIC 9(18) COMP-5.
             10 WS-R-BYTES PIC 9(18) COMP-5.
             10 WS-R-OK    PIC 9.
             10 WS-R-PIPE  PIC 9.
       01 WS-LABELS.
          05 WS-LABEL OCCURS 64 TIMES PIC X(256).
       01 WS-OPERANDS  PIC 9(4) COMP-5 VALUE 0.
       01 WS-ROWS-OK   PIC 9(4) COMP-5 VALUE 0.
       01 WS-PIPES     PIC 9(4) COMP-5 VALUE 0.
       01 WS-IMPLICIT  PIC 9 VALUE 0.
       01 WS-FAILED    PIC 9 VALUE 0.
       01 WS-IDX       PIC 9(4) COMP-5 VALUE 1.
       01 WS-TOTALS.
          05 WS-T-LINES PIC 9(18) COMP-5 VALUE 0.
          05 WS-T-WORDS PIC 9(18) COMP-5 VALUE 0.
          05 WS-T-BYTES PIC 9(18) COMP-5 VALUE 0.
       01 WS-WIDTH     PIC 9(9) COMP-5 VALUE 1.
       01 WS-FIGURES   PIC 9 VALUE 0.
       01 WS-POS       PIC 9(9) COMP-5 VALUE 1.
       01 WS-COL       PIC 9(9) COMP-5 VALUE 1.
       01 WS-DIGITS    PIC 9(9) COMP-5 VALUE 1.
       01 WS-N         PIC 9(9) COMP-5 VALUE 1.
       01 WS-EDIT      PIC Z(19)9.
       01 WS-TEXT      PIC X(256).
       01 WS-CELL      PIC X(32).
       01 WS-LINE      PIC X(400).
       01 WS-CHECK     PIC X(300).
       01 WS-RC        PIC S9(9) COMP-5.
       01 WS-BADFILE   PIC 9 VALUE 0.
       01 WS-PGM       PIC X(64) VALUE "{{ npm_name }}".
       01 WS-VERSION   PIC X(16) VALUE "0.1.0".
       LINKAGE SECTION.
       01 LK-PARSED.
          05 LK-STATUS PIC 9.
          05 LK-MESSAGE PIC X(120).
          05 LK-SHOW-L PIC 9.
          05 LK-SHOW-W PIC 9.
          05 LK-SHOW-C PIC 9.
          05 LK-NFILES PIC 9(4) COMP-5.
          05 LK-FILES.
             10 LK-FILE PIC X(256) OCCURS 64 TIMES.
       01 LK-RESULT    PIC 9(4) COMP-5.
       PROCEDURE DIVISION USING LK-PARSED LK-RESULT.
       MOVE 0 TO LK-RESULT
       EVALUATE LK-STATUS
         WHEN 2
           PERFORM PRINT-USAGE
         WHEN 3
           DISPLAY FUNCTION TRIM(WS-VERSION)
         WHEN 4
           PERFORM REFUSE
           MOVE 2 TO LK-RESULT
         WHEN OTHER
           PERFORM READ-OPERANDS
           PERFORM PRINT-ROWS
       END-EVALUATE
       GOBACK.

      *> --- outside world --------------------------------------------------
       PRINT-USAGE.
           DISPLAY "Usage: " FUNCTION TRIM(WS-PGM)
             " [OPTION]... [FILE]..."
           DISPLAY "Print newline, word, and byte counts for each FILE."
           DISPLAY SPACES
           DISPLAY "  -l, --lines    print the newline count"
           DISPLAY "  -w, --words    print the word count"
           DISPLAY "  -c, --bytes    print the byte count"
           DISPLAY "  -h, --help     show this help and exit"
           DISPLAY "  -V, --version  show the version and exit"
           DISPLAY SPACES
           DISPLAY "With no FILE, or when FILE is -, read standard input.".

       REFUSE.
           DISPLAY FUNCTION TRIM(WS-PGM) ": "
             FUNCTION TRIM(LK-MESSAGE) UPON STDERR
           DISPLAY "Try '" FUNCTION TRIM(WS-PGM)
             " --help' for more information." UPON STDERR.

      *> --- reading --------------------------------------------------------
       READ-OPERANDS.
           MOVE LK-NFILES TO WS-OPERANDS
           IF WS-OPERANDS = 0
             MOVE 1 TO WS-IMPLICIT
             MOVE 1 TO WS-ROWS-OK
             MOVE "-" TO WS-LABEL(1)
             MOVE "/dev/stdin" TO WS-PATH
             MOVE 1 TO WS-R-PIPE(1)
             PERFORM READ-ONE
           ELSE
             PERFORM VARYING WS-IDX FROM 1 BY 1 UNTIL WS-IDX > WS-OPERANDS
               MOVE LK-FILE(WS-IDX) TO WS-LABEL(WS-IDX)
               IF FUNCTION TRIM(WS-LABEL(WS-IDX)) = "-"
                 MOVE "/dev/stdin" TO WS-PATH
                 MOVE 1 TO WS-R-PIPE(WS-IDX)
               ELSE
                 MOVE LK-FILE(WS-IDX) TO WS-PATH
               END-IF
               PERFORM READ-ONE
             END-PERFORM
           END-IF.

       READ-ONE.
           MOVE 1 TO WS-OP
           MOVE 0 TO WS-BUFLEN
           MOVE SPACES TO WS-BUF
           CALL "TEXTSTAT-COUNTS" USING WS-OP WS-BUFLEN WS-BUF WS-COUNTS
           MOVE 0 TO WS-EOF
           MOVE 0 TO WS-BADFILE
           IF WS-R-PIPE(WS-IDX) = 0
      *> A directory opens cleanly and then reads nothing, so ask the shell
      *> whether this operand is a regular file before touching the FD.
             MOVE SPACES TO WS-CHECK
             STRING "test -f '" DELIMITED BY SIZE
                    FUNCTION TRIM(WS-PATH) DELIMITED BY SIZE
                    "' >/dev/null 2>&1" DELIMITED BY SIZE
                    INTO WS-CHECK
             END-STRING
             CALL "SYSTEM" USING WS-CHECK RETURNING WS-RC
             IF WS-RC NOT = 0
               MOVE 1 TO WS-BADFILE
             END-IF
           END-IF
           IF WS-BADFILE = 1
             MOVE 0 TO WS-R-OK(WS-IDX)
             MOVE 1 TO WS-FAILED
             DISPLAY "error: cannot open '"
               FUNCTION TRIM(WS-LABEL(WS-IDX)) "'" UPON STDERR
           ELSE
             OPEN INPUT F-DATA
             IF WS-FS NOT = "00"
               MOVE 0 TO WS-R-OK(WS-IDX)
               MOVE 1 TO WS-FAILED
               DISPLAY "error: cannot open '"
                 FUNCTION TRIM(WS-LABEL(WS-IDX)) "'" UPON STDERR
             ELSE
               MOVE 1 TO WS-R-OK(WS-IDX)
               MOVE 0 TO WS-BUFLEN
               PERFORM UNTIL WS-EOF = 1
                 READ F-DATA NEXT RECORD
                   AT END MOVE 1 TO WS-EOF
                   NOT AT END
                     IF WS-FS NOT = "00"
                       MOVE 1 TO WS-EOF
                       MOVE 1 TO WS-FAILED
                       MOVE 0 TO WS-R-OK(WS-IDX)
                       DISPLAY "error: cannot read '"
                         FUNCTION TRIM(WS-LABEL(WS-IDX)) "'" UPON STDERR
                     ELSE
                       ADD 1 TO WS-BUFLEN
                       MOVE F-BYTE TO WS-BUF(WS-BUFLEN:1)
                       IF WS-BUFLEN = 256
                         PERFORM FEED-BUFFER
                       END-IF
                     END-IF
                 END-READ
               END-PERFORM
               IF WS-BUFLEN > 0
                 PERFORM FEED-BUFFER
               END-IF
               CLOSE F-DATA
               MOVE WS-LINES TO WS-R-LINES(WS-IDX)
               MOVE WS-WORDS TO WS-R-WORDS(WS-IDX)
               MOVE WS-BYTES TO WS-R-BYTES(WS-IDX)
             END-IF
           END-IF.

       FEED-BUFFER.
           MOVE 2 TO WS-OP
           CALL "TEXTSTAT-COUNTS" USING WS-OP WS-BUFLEN WS-BUF WS-COUNTS
           MOVE 0 TO WS-BUFLEN
           MOVE SPACES TO WS-BUF.

      *> --- printing -------------------------------------------------------
       PRINT-ROWS.
           MOVE 0 TO WS-ROWS-OK WS-PIPES
           PERFORM VARYING WS-IDX FROM 1 BY 1
                   UNTIL WS-IDX > WS-OPERANDS OR WS-OPERANDS = 0
             IF WS-R-OK(WS-IDX) = 1
               ADD 1 TO WS-ROWS-OK
               ADD WS-R-BYTES(WS-IDX) TO WS-T-BYTES
               ADD WS-R-LINES(WS-IDX) TO WS-T-LINES
               ADD WS-R-WORDS(WS-IDX) TO WS-T-WORDS
               IF WS-R-PIPE(WS-IDX) = 1
                 ADD 1 TO WS-PIPES
               END-IF
             END-IF
           END-PERFORM
           IF WS-IMPLICIT = 1
             MOVE 1 TO WS-ROWS-OK
             ADD WS-R-BYTES(1) TO WS-T-BYTES
             ADD WS-R-LINES(1) TO WS-T-LINES
             ADD WS-R-WORDS(1) TO WS-T-WORDS
             IF WS-R-PIPE(1) = 1
               ADD 1 TO WS-PIPES
             END-IF
           END-IF
           PERFORM COMPUTE-WIDTH
           MOVE 1 TO WS-IDX
           PERFORM UNTIL WS-IDX > WS-OPERANDS AND WS-IMPLICIT = 0
             IF WS-R-OK(WS-IDX) = 1
               PERFORM PRINT-ROW
             END-IF
             ADD 1 TO WS-IDX
             IF WS-IMPLICIT = 1
               EXIT PERFORM
             END-IF
           END-PERFORM
           IF WS-OPERANDS > 1
             MOVE WS-T-LINES TO WS-R-LINES(1)
             MOVE WS-T-WORDS TO WS-R-WORDS(1)
             MOVE WS-T-BYTES TO WS-R-BYTES(1)
             MOVE 1 TO WS-R-OK(1)
             MOVE "total" TO WS-LABEL(1)
             MOVE 1 TO WS-R-PIPE(1)
             MOVE 1 TO WS-IDX
             PERFORM PRINT-ROW
           END-IF
           IF WS-FAILED = 1
             MOVE 1 TO LK-RESULT
           END-IF.

       COMPUTE-WIDTH.
           MOVE 1 TO WS-WIDTH
           COMPUTE WS-FIGURES = LK-SHOW-L + LK-SHOW-W + LK-SHOW-C
           IF WS-FIGURES = 1 AND WS-ROWS-OK <= 1
             PERFORM WIDTH-OF-ONE
           ELSE
             IF WS-PIPES > 0
               MOVE 7 TO WS-WIDTH
             ELSE
               MOVE WS-T-BYTES TO WS-EDIT
               MOVE FUNCTION TRIM(WS-EDIT) TO WS-TEXT
               COMPUTE WS-WIDTH =
                 FUNCTION LENGTH(FUNCTION TRIM(WS-TEXT))
               IF WS-WIDTH < 1
                 MOVE 1 TO WS-WIDTH
               END-IF
             END-IF
           END-IF.

      *> A lone figure on a lone row is printed at its natural width: wc
      *> does not pad it, so `wc -l` on a two-line file prints `2`, not ` 2`.
       WIDTH-OF-ONE.
           EVALUATE 1
             WHEN LK-SHOW-L
               MOVE WS-R-LINES(1) TO WS-EDIT
             WHEN LK-SHOW-W
               MOVE WS-R-WORDS(1) TO WS-EDIT
             WHEN OTHER
               MOVE WS-R-BYTES(1) TO WS-EDIT
           END-EVALUATE
           MOVE FUNCTION TRIM(WS-EDIT) TO WS-TEXT
           COMPUTE WS-WIDTH = FUNCTION LENGTH(FUNCTION TRIM(WS-TEXT))
           IF WS-WIDTH < 1
             MOVE 1 TO WS-WIDTH
           END-IF.

       PRINT-ROW.
           MOVE SPACES TO WS-LINE
           MOVE 1 TO WS-POS
           IF LK-SHOW-L = 1
             MOVE WS-R-LINES(WS-IDX) TO WS-EDIT
             PERFORM PUT-CELL
           END-IF
           IF LK-SHOW-W = 1
             MOVE WS-R-WORDS(WS-IDX) TO WS-EDIT
             PERFORM PUT-CELL
           END-IF
           IF LK-SHOW-C = 1
             MOVE WS-R-BYTES(WS-IDX) TO WS-EDIT
             PERFORM PUT-CELL
           END-IF
           IF WS-IMPLICIT = 0
             MOVE " " TO WS-LINE(WS-POS:1)
             ADD 1 TO WS-POS
             MOVE FUNCTION TRIM(WS-LABEL(WS-IDX)) TO WS-TEXT
             COMPUTE WS-N = FUNCTION LENGTH(FUNCTION TRIM(WS-TEXT))
             IF WS-N > 0
               MOVE WS-TEXT(1:WS-N) TO WS-LINE(WS-POS:WS-N)
               ADD WS-N TO WS-POS
             END-IF
           END-IF
           DISPLAY WS-LINE(1:WS-POS - 1).

       PUT-CELL.
           IF WS-POS > 1
             MOVE " " TO WS-LINE(WS-POS:1)
             ADD 1 TO WS-POS
           END-IF
           MOVE FUNCTION TRIM(WS-EDIT) TO WS-TEXT
           COMPUTE WS-DIGITS = FUNCTION LENGTH(FUNCTION TRIM(WS-TEXT))
           IF WS-DIGITS > WS-WIDTH
             MOVE WS-WIDTH TO WS-DIGITS
           END-IF
           MOVE SPACES TO WS-CELL
           COMPUTE WS-COL = WS-WIDTH - WS-DIGITS + 1
           MOVE WS-TEXT(1:WS-DIGITS) TO WS-CELL(WS-COL:WS-DIGITS)
           MOVE WS-CELL(1:WS-WIDTH) TO WS-LINE(WS-POS:WS-WIDTH)
           ADD WS-WIDTH TO WS-POS.

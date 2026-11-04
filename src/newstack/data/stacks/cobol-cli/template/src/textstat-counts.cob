       IDENTIFICATION DIVISION.
       PROGRAM-ID. TEXTSTAT-COUNTS.
      *> The counting core, and nothing else: it has no file, no terminal and
      *> no exit code, so the tests can hammer it without a process.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 WS-LINES   PIC 9(18) COMP-5 VALUE 0.
       01 WS-WORDS   PIC 9(18) COMP-5 VALUE 0.
       01 WS-BYTES   PIC 9(18) COMP-5 VALUE 0.
       01 WS-INWORD  PIC 9 VALUE 0.
       01 WS-SPACE   PIC 9 VALUE 0.
       01 WS-I       PIC 9(9) COMP-5.
       LINKAGE SECTION.
      *> op 1 = reset, op 2 = feed LK-LEN bytes from LK-BUF.
       01 LK-OP      PIC 9.
       01 LK-LEN     PIC 9(9) COMP-5.
       01 LK-BUF     PIC X(256).
       01 LK-COUNTS.
          05 LK-LINES PIC 9(18) COMP-5.
          05 LK-WORDS PIC 9(18) COMP-5.
          05 LK-BYTES PIC 9(18) COMP-5.
       PROCEDURE DIVISION USING LK-OP LK-LEN LK-BUF LK-COUNTS.
       EVALUATE LK-OP
         WHEN 1
           MOVE 0 TO WS-LINES WS-WORDS WS-BYTES WS-INWORD
         WHEN 2
           PERFORM VARYING WS-I FROM 1 BY 1 UNTIL WS-I > LK-LEN
             ADD 1 TO WS-BYTES
             MOVE 0 TO WS-SPACE
             EVALUATE LK-BUF(WS-I:1)
               WHEN X"0A"
                 ADD 1 TO WS-LINES
                 MOVE 1 TO WS-SPACE
               WHEN " "
                 MOVE 1 TO WS-SPACE
               WHEN X"09"
                 MOVE 1 TO WS-SPACE
               WHEN X"0D"
                 MOVE 1 TO WS-SPACE
               WHEN X"0B"
                 MOVE 1 TO WS-SPACE
               WHEN X"0C"
                 MOVE 1 TO WS-SPACE
               WHEN OTHER
                 CONTINUE
             END-EVALUATE
             IF WS-SPACE = 1
               MOVE 0 TO WS-INWORD
             ELSE
               IF WS-INWORD = 0
                 ADD 1 TO WS-WORDS
                 MOVE 1 TO WS-INWORD
               END-IF
             END-IF
           END-PERFORM
         WHEN OTHER
           CONTINUE
       END-EVALUATE
       MOVE WS-LINES TO LK-LINES
       MOVE WS-WORDS TO LK-WORDS
       MOVE WS-BYTES TO LK-BYTES
       GOBACK.

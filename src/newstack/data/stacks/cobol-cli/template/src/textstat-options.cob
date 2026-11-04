       IDENTIFICATION DIVISION.
       PROGRAM-ID. TEXTSTAT-OPTIONS.
      *> The argv parser. It takes the NUL-separated command line the caller
      *> read out of /proc/self/cmdline and turns it into a decision: carry on,
      *> print help, print the version, or refuse. No I/O of its own.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 WS-I         PIC 9(9) COMP-5.
       01 WS-J         PIC 9(9) COMP-5.
       01 WS-START     PIC 9(9) COMP-5.
       01 WS-WIDTH     PIC 9(9) COMP-5.
       01 WS-TOKEN     PIC X(256).
       01 WS-NAME      PIC X(256).
       01 WS-NAME-LEN  PIC 9(9) COMP-5.
       01 WS-ONLY      PIC 9 VALUE 0.
       01 WS-SEEN      PIC 9 VALUE 0.
       01 WS-K         PIC 9(9) COMP-5.
       01 WS-LETTER    PIC X(1).
       LINKAGE SECTION.
       01 LK-ARGV      PIC X(8192).
       01 LK-ARGV-LEN  PIC 9(9) COMP-5.
       01 LK-PARSED.
          05 LK-STATUS PIC 9.
          05 LK-MESSAGE PIC X(120).
          05 LK-SHOW-L PIC 9.
          05 LK-SHOW-W PIC 9.
          05 LK-SHOW-C PIC 9.
          05 LK-NFILES PIC 9(4) COMP-5.
          05 LK-FILES.
             10 LK-FILE PIC X(256) OCCURS 64 TIMES.
       PROCEDURE DIVISION USING LK-ARGV LK-ARGV-LEN LK-PARSED.
       MOVE 1 TO LK-STATUS
       MOVE SPACES TO LK-MESSAGE
       MOVE 0 TO LK-SHOW-L LK-SHOW-W LK-SHOW-C LK-NFILES WS-ONLY
       MOVE 0 TO WS-SEEN
       MOVE 1 TO WS-I
       PERFORM UNTIL WS-I > LK-ARGV-LEN
         MOVE WS-I TO WS-START
         PERFORM VARYING WS-J FROM WS-I BY 1
                 UNTIL WS-J > LK-ARGV-LEN
                    OR LK-ARGV(WS-J:1) = LOW-VALUE
           CONTINUE
         END-PERFORM
         COMPUTE WS-WIDTH = WS-J - WS-START
         MOVE SPACES TO WS-TOKEN
         IF WS-WIDTH > 0 AND WS-WIDTH <= 256
           MOVE LK-ARGV(WS-START:WS-WIDTH) TO WS-TOKEN
         END-IF
         COMPUTE WS-I = WS-J + 1
      *> the first word is the program's own name, not an argument
         IF WS-START = 1
           CONTINUE
         ELSE
           IF WS-WIDTH > 0
             IF WS-ONLY = 1
               PERFORM ADD-FILE
             ELSE
               IF WS-TOKEN(1:1) = "-" AND WS-WIDTH = 1
                 PERFORM ADD-FILE
               ELSE
                 IF WS-TOKEN(1:2) = "--" AND WS-WIDTH = 2
                   MOVE 1 TO WS-ONLY
                 ELSE
                   IF WS-TOKEN(1:2) = "--"
                     PERFORM LONG-OPTION
                   ELSE
                     IF WS-TOKEN(1:1) = "-"
                       PERFORM SHORT-OPTIONS
                     ELSE
                       PERFORM ADD-FILE
                     END-IF
                   END-IF
                 END-IF
               END-IF
             END-IF
           END-IF
         END-IF
       END-PERFORM
       IF LK-STATUS = 1 AND WS-SEEN = 0
         MOVE 1 TO LK-SHOW-L LK-SHOW-W LK-SHOW-C
       END-IF
       GOBACK.

       ADD-FILE.
           IF LK-NFILES >= 64
             MOVE 4 TO LK-STATUS
             MOVE "too many file operands" TO LK-MESSAGE
           ELSE
             ADD 1 TO LK-NFILES
             MOVE SPACES TO LK-FILE(LK-NFILES)
             MOVE WS-TOKEN(1:WS-WIDTH) TO LK-FILE(LK-NFILES)
           END-IF.

       LONG-OPTION.
           COMPUTE WS-NAME-LEN = WS-WIDTH - 2
           MOVE SPACES TO WS-NAME
           MOVE WS-TOKEN(3:WS-NAME-LEN) TO WS-NAME
           EVALUATE FUNCTION TRIM(WS-NAME)
             WHEN "lines"
               MOVE 1 TO LK-SHOW-L
               MOVE 1 TO WS-SEEN
             WHEN "words"
               MOVE 1 TO LK-SHOW-W
               MOVE 1 TO WS-SEEN
             WHEN "bytes"
               MOVE 1 TO LK-SHOW-C
               MOVE 1 TO WS-SEEN
             WHEN "help"
               MOVE 2 TO LK-STATUS
             WHEN "version"
               MOVE 3 TO LK-STATUS
             WHEN OTHER
               MOVE 4 TO LK-STATUS
               MOVE SPACES TO LK-MESSAGE
               STRING "unknown option: " FUNCTION TRIM(WS-TOKEN)
                 INTO LK-MESSAGE
           END-EVALUATE.

       SHORT-OPTIONS.
           PERFORM VARYING WS-K FROM 2 BY 1 UNTIL WS-K > WS-WIDTH
             MOVE WS-TOKEN(WS-K:1) TO WS-LETTER
             EVALUATE WS-LETTER
               WHEN "l"
                 MOVE 1 TO LK-SHOW-L
                 MOVE 1 TO WS-SEEN
               WHEN "w"
                 MOVE 1 TO LK-SHOW-W
                 MOVE 1 TO WS-SEEN
               WHEN "c"
                 MOVE 1 TO LK-SHOW-C
                 MOVE 1 TO WS-SEEN
               WHEN "h"
                 MOVE 2 TO LK-STATUS
               WHEN "V"
                 MOVE 3 TO LK-STATUS
               WHEN OTHER
                 MOVE 4 TO LK-STATUS
                 MOVE SPACES TO LK-MESSAGE
                 STRING "unknown option: -" WS-LETTER INTO LK-MESSAGE
             END-EVALUATE
           END-PERFORM.

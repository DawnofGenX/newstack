       IDENTIFICATION DIVISION.
       PROGRAM-ID. TEXTSTAT-MAIN.
      *> The process-facing entry point: it reads the process's own command
      *> line, asks TEXTSTAT-OPTIONS what it means, and hands that to
      *> TEXTSTAT-RUNNER. Every exit code the tool has is set right here.
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT F-CMDLINE ASSIGN TO "/proc/self/cmdline"
               ORGANIZATION IS SEQUENTIAL
               FILE STATUS IS WS-FS.
       DATA DIVISION.
       FILE SECTION.
       FD F-CMDLINE.
       01 F-BYTE PIC X(1).
       WORKING-STORAGE SECTION.
       01 WS-FS        PIC X(2).
       01 WS-EOF       PIC 9 VALUE 0.
       01 WS-ARGV      PIC X(8192).
       01 WS-ARGV-LEN  PIC 9(9) COMP-5 VALUE 0.
       01 WS-RESULT    PIC 9(4) COMP-5 VALUE 0.
       01 WS-PARSED.
          05 WS-STATUS PIC 9.
          05 WS-MESSAGE PIC X(120).
          05 WS-SHOW-L PIC 9.
          05 WS-SHOW-W PIC 9.
          05 WS-SHOW-C PIC 9.
          05 WS-NFILES PIC 9(4) COMP-5.
          05 WS-FILES.
             10 WS-FILE PIC X(256) OCCURS 64 TIMES.
       PROCEDURE DIVISION.
       MOVE SPACES TO WS-ARGV
       OPEN INPUT F-CMDLINE
       IF WS-FS = "00"
         PERFORM UNTIL WS-EOF = 1
           READ F-CMDLINE NEXT RECORD
             AT END MOVE 1 TO WS-EOF
             NOT AT END
               IF WS-ARGV-LEN < 8192
                 ADD 1 TO WS-ARGV-LEN
                 MOVE F-BYTE TO WS-ARGV(WS-ARGV-LEN:1)
               END-IF
           END-READ
         END-PERFORM
         CLOSE F-CMDLINE
       END-IF
       CALL "TEXTSTAT-OPTIONS" USING WS-ARGV WS-ARGV-LEN WS-PARSED
       CALL "TEXTSTAT-RUNNER" USING WS-PARSED WS-RESULT
       MOVE WS-RESULT TO RETURN-CODE
       GOBACK.

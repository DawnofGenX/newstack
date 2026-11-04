--  The suite: no framework, one harness, fixtures written byte for byte.
with Ada.Directories;
with Ada.Streams;
with Ada.Streams.Stream_IO;
with Ada.Strings.Unbounded;


with Harness;
with Textstat.Counts;
with Textstat.Options;
with Textstat.Runner;

procedure Run_Tests is
   use Harness;
   use Textstat.Counts;
   use Textstat.Options;
   use Textstat.Runner;

   Fixtures : constant String := "fixtures-tmp";
   Alpha    : constant String := Fixtures & "/alpha.txt";
   Beta     : constant String := Fixtures & "/beta.txt";
   Missing  : constant String := Fixtures & "/nope.txt";

   function Arg (Text : String) return Ada.Strings.Unbounded.Unbounded_String
     renames Ada.Strings.Unbounded.To_Unbounded_String;

   procedure Write_File (Path, Data : String) is
      use Ada.Streams.Stream_IO;
      File : File_Type;
   begin
      --  Stream_IO, not Text_IO: closing a Text_IO out file appends a line
      --  terminator, which would make every fixture one byte too long.
      Create (File, Out_File, Path);
      String'Write (Stream (File), Data);
      Close (File);
   end Write_File;

   procedure Counts_Tests is
      Plain  : constant String := "alpha beta" & ASCII.LF & "gamma delta" & ASCII.LF;
      Utf8   : constant String := "h" & Character'Val (16#C3#) & Character'Val (16#A9#)
                                   & "llo w" & Character'Val (16#C3#)
                                   & Character'Val (16#B6#) & "rld" & ASCII.LF;
      Control : constant String := "a" & ASCII.HT & "b" & ASCII.VT & "c" & ASCII.FF
                                   & "d" & ASCII.LF;
      Plain_Counts : constant Tally := Of_String (Plain);
      Doubled      : constant Tally := Plain_Counts + Plain_Counts;
   begin
      Check_Int ("plain lines", Plain_Counts.Lines, 2);
      Check_Int ("plain words", Plain_Counts.Words, 4);
      Check_Int ("plain bytes", Plain_Counts.Bytes, 23);
      Check_Int ("empty bytes", Of_String ("").Bytes, 0);
      Check_Int ("empty words", Of_String ("").Words, 0);
      Check_Int ("unterminated words", Of_String ("one two three").Words, 3);
      Check_Int ("unterminated lines", Of_String ("one two three").Lines, 0);
      Check_Int ("unterminated bytes", Of_String ("one two three").Bytes, 13);
      Check_Int ("utf8 bytes", Of_String (Utf8).Bytes, 14);
      Check_Int ("utf8 words", Of_String (Utf8).Words, 2);
      Check_Int ("utf8 lines", Of_String (Utf8).Lines, 1);
      Check_Int ("control words", Of_String (Control).Words, 4);
      Check_Int ("control bytes", Of_String (Control).Bytes, 8);
      Check ("space is a separator", Is_Space (' '));
      Check ("tab is a separator", Is_Space (ASCII.HT));
      Check ("newline is a separator", Is_Space (ASCII.LF));
      Check ("vertical tab is a separator", Is_Space (ASCII.VT));
      Check ("form feed is a separator", Is_Space (ASCII.FF));
      Check ("carriage return is a separator", Is_Space (ASCII.CR));
      Check ("letter is not a separator", not Is_Space ('a'));
      Check ("underscore is not a separator", not Is_Space ('_'));
      declare
         Zeroed : constant Tally := Empty + Empty;
      begin
         Check_Int ("empty plus empty", Zeroed.Bytes, 0);
      end;
      Check_Int ("add lines", Doubled.Lines, 4);
      Check_Int ("add words", Doubled.Words, 8);
      Check_Int ("add bytes", Doubled.Bytes, 46);
      Check_Text ("image of zero", Image (0), "0");
      Check_Text ("image of 42", Image (42), "42");
      Check_Int ("all figures has three columns", Long_Long_Integer (Column_Count (All_Figures)), 3);
      Check_Int ("no figures has none", Long_Long_Integer (Column_Count (No_Figures)), 0);
      Check_Int ("two figures", Long_Long_Integer (Column_Count ((Lines => True, Words => False, Bytes => True))), 2);
   end Counts_Tests;

   procedure Options_Tests is
      Bare    : constant Parsed := Parse ((1 => Arg ("--help")));
      Cluster : constant Parsed := Parse ((1 => Arg ("-lw"), 2 => Arg ("alpha.txt")));
      Termin  : constant Parsed := Parse ((1 => Arg ("--"), 2 => Arg ("-l")));
      Dashed  : constant Parsed := Parse ((1 => Arg ("-")));
      Bad     : constant Parsed := Parse ((1 => Arg ("--bogus")));
      Bad_Key : constant Parsed := Parse ((1 => Arg ("-x")));
      Files   : constant Parsed := Parse ((1 => Arg ("--lines"),
                                          2 => Arg ("alpha.txt"),
                                          3 => Arg ("beta.txt")));
      Repeat  : constant Parsed := Parse ((1 => Arg ("-l"), 2 => Arg ("--lines")));
   begin
      Check ("help short circuits", Bare.State = Help);
      Check_Text ("usage names the program", Usage ("prog") (1 .. 9), "Usage: pr");
      Check ("usage mentions the flags", Ada.Strings.Unbounded.Index (Arg (Usage ("prog")), "[-l] [-w] [-c]") > 0);
      Check ("cluster sets lines", Cluster.Figures (Lines));
      Check ("cluster sets words", Cluster.Figures (Words));
      Check ("cluster leaves bytes alone", not Cluster.Figures (Bytes));
      Check_Int ("cluster keeps the file", Long_Long_Integer (Cluster.Files.Length), 1);
      Check_Int ("cluster one column", Long_Long_Integer (Column_Count (Cluster.Figures)), 2);
      Check ("terminator files the dash flag", Long_Long_Integer (Termin.Files.Length) = 1);
      Check_Text ("terminator keeps the literal", Ada.Strings.Unbounded.To_String (Termin.Files (1)), "-l");
      Check ("terminator means all figures", Long_Long_Integer (Column_Count (Termin.Figures)) = 3);
      Check_Int ("a lone dash is one operand", Long_Long_Integer (Dashed.Files.Length), 1);
      Check_Text ("a lone dash is stdin", Ada.Strings.Unbounded.To_String (Dashed.Files (1)), "-");
      Check ("bad long option is a usage error", Bad.State = Usage_Error);
      Check_Text ("bad long option message",
                  Ada.Strings.Unbounded.To_String (Bad.Message), "unknown option: --bogus");
      Check ("bad short option is a usage error", Bad_Key.State = Usage_Error);
      Check_Text ("bad short option message",
                  Ada.Strings.Unbounded.To_String (Bad_Key.Message), "unknown option: -x");
      Check_Int ("two operands kept in order", Long_Long_Integer (Files.Files.Length), 2);
      Check_Text ("first operand", Ada.Strings.Unbounded.To_String (Files.Files (1)), "alpha.txt");
      Check_Text ("second operand", Ada.Strings.Unbounded.To_String (Files.Files (2)), "beta.txt");
      Check_Int ("repeated flag is still one column", Long_Long_Integer (Column_Count (Repeat.Figures)), 1);
      Check ("no flag means every figure", Column_Count (Parse ((1 => Arg ("alpha.txt"))).Figures) = 3);
   end Options_Tests;

   procedure Runner_Tests is
      Code : Integer := 0;
   begin
      Reset;
      Code := Run ((1 => Arg ("--help")), Harness.Write_Out'Access, Harness.Write_Err'Access);
      Check_Int ("help exit code", Long_Long_Integer (Code), 0);
      Check_Text ("help text", Out_Text, Usage (Program) & ASCII.LF);

      Reset;
      Code := Run ((1 => Arg ("--version")), Harness.Write_Out'Access, Harness.Write_Err'Access);
      Check_Int ("version exit code", Long_Long_Integer (Code), 0);
      Check_Text ("version text", Out_Text, "0.1.0" & ASCII.LF);

      Reset;
      Code := Run ((1 => Arg ("--bogus")), Harness.Write_Out'Access, Harness.Write_Err'Access);
      Check_Int ("usage error exit code", Long_Long_Integer (Code), 2);
      Check_Text ("usage error is two lines", Err_Text,
                  Program & ": unknown option: --bogus" & ASCII.LF
                  & "Try '" & Program & " --help' for more information." & ASCII.LF);
      Check_Text ("usage error prints nothing on stdout", Out_Text, "");

      Reset;
      Code := Run ((1 => Arg ("-l"), 2 => Arg ("-w"), 3 => Arg ("-c"), 4 => Arg (Alpha)),
                   Harness.Write_Out'Access, Harness.Write_Err'Access);
      Check_Int ("one file exit code", Long_Long_Integer (Code), 0);
      Check_Text ("one file row", Out_Text, " 2  4 23 " & Alpha & ASCII.LF);

      Reset;
      Code := Run ((1 => Arg ("-w"), 2 => Arg (Alpha)),
                   Harness.Write_Out'Access, Harness.Write_Err'Access);
      Check_Int ("single figure exit code", Long_Long_Integer (Code), 0);
      Check_Text ("single figure row", Out_Text, "4 " & Alpha & ASCII.LF);

      Reset;
      Code := Run ((1 => Arg (Missing)), Harness.Write_Out'Access, Harness.Write_Err'Access);
      Check_Int ("missing file exit code", Long_Long_Integer (Code), 1);
      Check_Text ("missing file message", Err_Text, "error: cannot open '" & Missing & "'" & ASCII.LF);
      Check_Text ("missing file prints no row", Out_Text, "");

      Reset;
      Code := Run ((1 => Arg (Alpha), 2 => Arg (Beta)),
                   Harness.Write_Out'Access, Harness.Write_Err'Access);
      Check_Int ("two files exit code", Long_Long_Integer (Code), 0);
      Check_Text ("two files rows", Out_Text,
                  " 2  4 23 " & Alpha & ASCII.LF
                  & " 0  3 13 " & Beta & ASCII.LF
                  & " 2  7 36 total" & ASCII.LF);

      Reset;
      Code := Run ((1 => Arg (Missing), 2 => Arg (Alpha)),
                   Harness.Write_Out'Access, Harness.Write_Err'Access);
      Check_Int ("one bad operand still exits 1", Long_Long_Integer (Code), 1);
      Check_Text ("one bad operand keeps the row", Out_Text,
                  " 2  4 23 " & Alpha & ASCII.LF & " 2  4 23 total" & ASCII.LF);
      Check_Text ("one bad operand complains", Err_Text,
                  "error: cannot open '" & Missing & "'" & ASCII.LF);
   end Runner_Tests;

begin
   Ada.Directories.Create_Path (Fixtures);
   Write_File (Alpha, "alpha beta" & ASCII.LF & "gamma delta" & ASCII.LF);
   Write_File (Beta, "one two three");

   Counts_Tests;
   Options_Tests;
   Runner_Tests;

   Ada.Directories.Delete_Tree (Fixtures);
   Report;
end Run_Tests;

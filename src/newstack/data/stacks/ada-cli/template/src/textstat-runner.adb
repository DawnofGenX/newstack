with Ada.Streams;
with Ada.Streams.Stream_IO;
with Ada.Strings.Unbounded; use Ada.Strings.Unbounded;

with Textstat.Counts;  use Textstat.Counts;
with Textstat.Options; use Textstat.Options;

package body Textstat.Runner is

   Chunk_Size : constant := 4096;

   function Read_All (Path : String; Ok : out Boolean) return Unbounded_String is
      use Ada.Streams;
      use Ada.Streams.Stream_IO;
      File   : File_Type;
      Buffer : Stream_Element_Array (1 .. Chunk_Size);
      Last   : Stream_Element_Offset;
      Text   : Unbounded_String;
   begin
      Ok := False;
      if Path'Length = 0 then
         return Null_Unbounded_String;
      end if;
      --  A lone dash is standard input, exactly like wc.
      if Path = "-" then
         Ada.Streams.Stream_IO.Open (File, In_File, "/dev/stdin");
      else
         Ada.Streams.Stream_IO.Open (File, In_File, Path);
      end if;
      loop
         Read (File, Buffer, Last);
         exit when Last < Buffer'First;
         for I in Buffer'First .. Last loop
            Append (Text, Character'Val (Buffer (I)));
         end loop;
      end loop;
      Close (File);
      Ok := True;
      return Text;
   exception
      when others =>
         if Is_Open (File) then
            Close (File);
         end if;
         Ok := False;
         return Null_Unbounded_String;
   end Read_All;

   function Value (C : Tally; F : Figure) return Long_Long_Integer is
   begin
      case F is
         when Lines => return C.Lines;
         when Words => return C.Words;
         when Bytes => return C.Bytes;
      end case;
   end Value;

   function Width_Of (N : Long_Long_Integer) return Natural is
      --  Digits is a reserved word in Ada, hence the name.
   begin
      return Image (N)'Length;
   end Width_Of;

   function Max (Left, Right : Natural) return Natural is
   begin
      if Left > Right then
         return Left;
      end if;
      return Right;
   end Max;

   function Pad (Text : String; Width : Natural) return String is
   begin
      if Text'Length >= Width then
         return Text;
      end if;
      declare
         Blanks : constant String (1 .. Width - Text'Length) := (others => ' ');
      begin
         return Blanks & Text;
      end;
   end Pad;

   function Row_Text (C : Tally; Set : Figure_Set; Width : Natural) return String is
      Row : Unbounded_String;
   begin
      for F in Figure loop
         if Set (F) then
            if Length (Row) > 0 then
               Append (Row, " ");
            end if;
            Append (Row, Pad (Image (Value (C, F)), Width));
         end if;
      end loop;
      return To_String (Row);
   end Row_Text;

   function Run (Args : Textstat.Options.Arg_Array;
                 Out_Write, Err_Write : Writer) return Integer is
      Opts : constant Parsed := Parse (Args);

      procedure Put (Text : String) is
      begin
         Out_Write.all (Text);
      end Put;

      procedure Put_Error (Text : String) is
      begin
         Err_Write.all (Text);
      end Put_Error;
   begin
      case Opts.State is
         when Help =>
            Put (Usage (Program));
            return 0;
         when Version =>
            Put (Textstat.Options.Tool_Version);
            return 0;
         when Usage_Error =>
            Put_Error (Program & ": " & To_String (Opts.Message));
            Put_Error ("Try '" & Program & " --help' for more information.");
            return 2;
         when Ok =>
            null;
      end case;

      declare
         Count  : constant Natural := Natural (Opts.Files.Length);
         Labels : array (1 .. Count) of Unbounded_String;
         Rows   : array (1 .. Count) of Tally;
         Failed : array (1 .. Count) of Boolean := (others => False);
         Total  : Tally := Empty;
         Width  : Natural := 1;
         Any_Bad : Boolean := False;
      begin
         for I in 1 .. Count loop
            Labels (I) := Opts.Files.Element (I);
         end loop;
         if Count = 0 then
            --  No FILE operand reads standard input, labelled like wc does.
            declare
               Data : Unbounded_String;
               Ok   : Boolean;
            begin
               Data := Read_All ("/dev/stdin", Ok);
               if not Ok then
                  Put_Error ("error: cannot open '-'");
                  return 1;
               end if;
               declare
                  Row   : constant Tally := Of_String (To_String (Data));
                  Width : Natural := 1;
               begin
                  for F in Figure loop
                     if Opts.Figures (F) then
                        Width := Max (Width, Width_Of (Value (Row, F)));
                     end if;
                  end loop;
                  Put (Row_Text (Row, Opts.Figures, Width) & " -");
                  return 0;
               end;
            end;
         end if;

         for I in 1 .. Count loop
            declare
               Path : constant String := To_String (Labels (I));
               Ok   : Boolean;
               Data : Unbounded_String;
            begin
               Data := Read_All (Path, Ok);
               if not Ok then
                  Put_Error ("error: cannot open '" & Path & "'");
                  Failed (I) := True;
                  Any_Bad := True;
                  Rows (I) := Empty;
               else
                  Rows (I) := Of_String (To_String (Data));
                  Total := Total + Rows (I);
               end if;
            end;
         end loop;

         for I in 1 .. Count loop
            if not Failed (I) then
               for F in Figure loop
                  if Opts.Figures (F) then
                     Width := Max (Width, Width_Of (Value (Rows (I), F)));
                  end if;
               end loop;
            end if;
         end loop;
         if Count > 1 then
            for F in Figure loop
               if Opts.Figures (F) then
                  Width := Max (Width, Width_Of (Value (Total, F)));
               end if;
            end loop;
         end if;

         for I in 1 .. Count loop
            if not Failed (I) then
               Put (Row_Text (Rows (I), Opts.Figures, Width) & " " & To_String (Labels (I)));
            end if;
         end loop;
         if Count > 1 then
            Put (Row_Text (Total, Opts.Figures, Width) & " total");
         end if;

         if Any_Bad then
            return 1;
         end if;
         return 0;
      end;
   end Run;

end Textstat.Runner;

package body Textstat.Options is

   function Usage (Program : String) return String is
   begin
      return "Usage: " & Program & " [-l] [-w] [-c] [FILE...]"
        & ASCII.LF
        & "Count lines, words and bytes. With no FILE, or with -, read stdin.";
   end Usage;

   function Parse (Args : Arg_Array) return Parsed is
      Result           : Parsed;
      After_Terminator : Boolean := False;
      Any_Figure       : Boolean := False;

      procedure Add_Figure (F : Textstat.Counts.Figure) is
      begin
         Result.Figures (F) := True;
         Any_Figure := True;
      end Add_Figure;

      procedure Fail (Text : String) is
      begin
         Result.State := Usage_Error;
         Result.Message := To_Unbounded_String (Text);
      end Fail;
   begin
      if Args'Length = 0 then
         Result.Figures := Textstat.Counts.All_Figures;
         return Result;
      end if;

      for I in Args'Range loop
         declare
            Arg : constant String := To_String (Args (I));
         begin
            if After_Terminator then
               Result.Files.Append (Args (I));
            elsif Arg = "--" then
               After_Terminator := True;
            elsif Arg = "--lines" then
               Add_Figure (Textstat.Counts.Lines);
            elsif Arg = "--words" then
               Add_Figure (Textstat.Counts.Words);
            elsif Arg = "--bytes" then
               Add_Figure (Textstat.Counts.Bytes);
            elsif Arg = "--help" then
               Result.State := Help;
               return Result;
            elsif Arg = "--version" then
               Result.State := Version;
               return Result;
            elsif Arg'Length > 2 and then Arg (Arg'First .. Arg'First + 1) = "--" then
               Fail ("unknown option: " & Arg);
               return Result;
            elsif Arg = "-" then
               Result.Files.Append (Args (I));
            elsif Arg'Length > 1 and then Arg (Arg'First) = '-' then
               for J in Arg'First + 1 .. Arg'Last loop
                  case Arg (J) is
                     when 'l' =>
                        Add_Figure (Textstat.Counts.Lines);
                     when 'w' =>
                        Add_Figure (Textstat.Counts.Words);
                     when 'c' =>
                        Add_Figure (Textstat.Counts.Bytes);
                     when 'h' =>
                        Result.State := Help;
                        return Result;
                     when 'V' =>
                        Result.State := Version;
                        return Result;
                     when others =>
                        Fail ("unknown option: -" & Arg (J));
                        return Result;
                  end case;
               end loop;
            else
               Result.Files.Append (Args (I));
            end if;
         end;
      end loop;

      if not Any_Figure then
         Result.Figures := Textstat.Counts.All_Figures;
      end if;
      return Result;
   end Parse;

end Textstat.Options;

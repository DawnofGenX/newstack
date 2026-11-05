package body Textstat.Counts is

   function Is_Space (Item : Character) return Boolean is
      Code : constant Natural := Character'Pos (Item);
   begin
      return Item = ' '
        or else Item = ASCII.HT
        or else Item = ASCII.LF
        or else Item = ASCII.CR
        or else Code = 11
        or else Code = 12;
   end Is_Space;

   function Count_Text (Text : String) return Counts is
      Result : Counts := (Lines => 0, Words => 0, Bytes => Text'Length);
      In_Word : Boolean := False;
   begin
      for Index in Text'Range loop
         if Text (Index) = ASCII.LF then
            Result.Lines := Result.Lines + 1;
         end if;
         if Is_Space (Text (Index)) then
            In_Word := False;
         elsif not In_Word then
            Result.Words := Result.Words + 1;
            In_Word := True;
         end if;
      end loop;
      return Result;
   end Count_Text;

end Textstat.Counts;

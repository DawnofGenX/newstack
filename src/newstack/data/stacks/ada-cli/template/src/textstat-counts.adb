package body Textstat.Counts is

   function "+" (Left, Right : Tally) return Tally is
   begin
      return (Lines => Left.Lines + Right.Lines,
              Words => Left.Words + Right.Words,
              Bytes => Left.Bytes + Right.Bytes);
   end "+";

   function Is_Space (C : Character) return Boolean is
   begin
      return C = ' ' or else C = ASCII.HT or else C = ASCII.LF
        or else C = ASCII.VT or else C = ASCII.FF or else C = ASCII.CR;
   end Is_Space;

   function Of_String (Data : String) return Tally is
      Result  : Tally := Empty;
      In_Word : Boolean := False;
   begin
      for C of Data loop
         Result.Bytes := Result.Bytes + 1;
         if C = ASCII.LF then
            Result.Lines := Result.Lines + 1;
         end if;
         if Is_Space (C) then
            In_Word := False;
         elsif not In_Word then
            In_Word := True;
            Result.Words := Result.Words + 1;
         end if;
      end loop;
      return Result;
   end Of_String;

   function Column_Count (Set : Figure_Set) return Natural is
      Total : Natural := 0;
   begin
      for F in Figure loop
         if Set (F) then
            Total := Total + 1;
         end if;
      end loop;
      return Total;
   end Column_Count;

   function Image (Value : Long_Long_Integer) return String is
      Raw : constant String := Long_Long_Integer'Image (Value);
   begin
      --  'Image puts a leading space on a non-negative value; drop it.
      if Raw (Raw'First) = ' ' then
         return Raw (Raw'First + 1 .. Raw'Last);
      end if;
      return Raw;
   end Image;

end Textstat.Counts;

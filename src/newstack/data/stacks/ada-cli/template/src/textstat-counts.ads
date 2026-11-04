--  The counting core: no I/O, no exceptions, just bytes in and figures out.
package Textstat.Counts is

   type Figure is (Lines, Words, Bytes);

   type Figure_Set is array (Figure) of Boolean;

   All_Figures : constant Figure_Set := (others => True);
   No_Figures  : constant Figure_Set := (others => False);

   type Tally is record
      Lines : Long_Long_Integer := 0;
      Words : Long_Long_Integer := 0;
      Bytes : Long_Long_Integer := 0;
   end record;

   Empty : constant Tally := (Lines => 0, Words => 0, Bytes => 0);

   function "+" (Left, Right : Tally) return Tally;

   function Is_Space (C : Character) return Boolean;
   --  True for the six bytes wc treats as word separators.

   function Of_String (Data : String) return Tally;
   --  Bytes counted with Data'Length, lines with the newline byte, words with
   --  maximal runs of non-space bytes (so an unterminated last line still has
   --  its words).

   function Column_Count (Set : Figure_Set) return Natural;

   function Image (Value : Long_Long_Integer) return String;

end Textstat.Counts;

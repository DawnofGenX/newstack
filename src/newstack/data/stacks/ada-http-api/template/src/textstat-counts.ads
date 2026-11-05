package Textstat.Counts is

   type Counts is record
      Lines : Natural := 0;
      Words : Natural := 0;
      Bytes : Natural := 0;
   end record;

   --  wc rules: a line ends at ASCII.LF, a word is a maximal run of
   --  non-space characters, and Bytes counts the UTF-8 bytes handed in.
   function Count_Text (Text : String) return Counts;

end Textstat.Counts;

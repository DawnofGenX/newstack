--  Argv parsing, kept free of I/O so the suite can call it directly.
with Ada.Containers.Vectors;
with Ada.Strings.Unbounded;
use Ada.Strings.Unbounded;

with Textstat.Counts;

package Textstat.Options is

   package File_Vectors is new Ada.Containers.Vectors
     (Index_Type   => Positive,
      Element_Type => Ada.Strings.Unbounded.Unbounded_String);

   --  The command line, reshaped as a plain array so tests can build one.
   type Arg_Array is array (Positive range <>) of Ada.Strings.Unbounded.Unbounded_String;

   type Status is (Ok, Help, Version, Usage_Error);

   type Parsed is record
      State   : Status := Ok;
      Figures : Textstat.Counts.Figure_Set := Textstat.Counts.No_Figures;
      Files   : File_Vectors.Vector;
      Message : Ada.Strings.Unbounded.Unbounded_String;
   end record;

   Tool_Version : constant String := "0.1.0";
   --  Not Version: that is also a Status literal in this package.

   function Usage (Program : String) return String;

   function Parse (Args : Arg_Array) return Parsed;
   --  Figures default to all three when no figure flag was given.

end Textstat.Options;

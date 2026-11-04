--  A four-procedure test harness: no dependency, no framework, same shape as
--  the other newstack CLI stacks. Library level so Runner can take 'Access.
with Ada.Strings.Unbounded;

package Harness is

   Passed : Natural := 0;
   Failed : Natural := 0;

   Out_Buf : Ada.Strings.Unbounded.Unbounded_String;
   Err_Buf : Ada.Strings.Unbounded.Unbounded_String;

   procedure Write_Out (Text : String);
   procedure Write_Err (Text : String);

   procedure Reset;
   --  Clear both capture buffers before a Runner call.

   procedure Check (Name : String; Ok : Boolean; Detail : String := "");
   procedure Check_Text (Name : String; Actual : String; Expected : String);
   procedure Check_Int (Name : String; Actual : Long_Long_Integer; Expected : Long_Long_Integer);

   function Out_Text return String;
   function Err_Text return String;

   procedure Report;
   --  Prints one tally line and sets the exit status.

end Harness;

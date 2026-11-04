with Ada.Command_Line;
with Ada.Strings;
with Ada.Strings.Unbounded;
with Ada.Text_IO;
use Ada.Strings.Unbounded;

package body Harness is

   procedure Write_Out (Text : String) is
   begin
      Append (Out_Buf, Text);
      Append (Out_Buf, ASCII.LF);
   end Write_Out;

   procedure Write_Err (Text : String) is
   begin
      Append (Err_Buf, Text);
      Append (Err_Buf, ASCII.LF);
   end Write_Err;

   procedure Reset is
   begin
      Out_Buf := Null_Unbounded_String;
      Err_Buf := Null_Unbounded_String;
   end Reset;

   procedure Check (Name : String; Ok : Boolean; Detail : String := "") is
   begin
      if Ok then
         Passed := Passed + 1;
      else
         Failed := Failed + 1;
         Ada.Text_IO.Put_Line ("FAIL " & Name);
         if Detail'Length > 0 then
            Ada.Text_IO.Put_Line ("     " & Detail);
         end if;
      end if;
   end Check;

   procedure Check_Text (Name : String; Actual : String; Expected : String) is
   begin
      if Actual = Expected then
         Check (Name, True);
      else
         Check (Name, False, "got [" & Actual & "] want [" & Expected & "]");
      end if;
   end Check_Text;

   procedure Check_Int (Name : String; Actual : Long_Long_Integer; Expected : Long_Long_Integer) is
   begin
      if Actual = Expected then
         Check (Name, True);
      else
         Check (Name, False,
                "got " & Long_Long_Integer'Image (Actual)
                & " want " & Long_Long_Integer'Image (Expected));
      end if;
   end Check_Int;

   function Out_Text return String is
   begin
      return To_String (Out_Buf);
   end Out_Text;

   function Err_Text return String is
   begin
      return To_String (Err_Buf);
   end Err_Text;

   procedure Report is
   begin
      Ada.Text_IO.Put_Line
        ("checks: " & Natural'Image (Passed + Failed)
         & ", passed: " & Natural'Image (Passed)
         & ", failed: " & Natural'Image (Failed));
      if Failed = 0 then
         Ada.Command_Line.Set_Exit_Status (0);
      else
         Ada.Command_Line.Set_Exit_Status (1);
      end if;
   end Report;

end Harness;

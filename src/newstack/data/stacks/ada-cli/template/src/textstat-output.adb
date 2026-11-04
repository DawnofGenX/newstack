with Ada.Text_IO;

package body Textstat.Output is

   procedure Write_Out (Text : String) is
   begin
      Ada.Text_IO.Put_Line (Text);
   end Write_Out;

   procedure Write_Err (Text : String) is
   begin
      Ada.Text_IO.Put_Line (Ada.Text_IO.Standard_Error, Text);
   end Write_Err;

end Textstat.Output;

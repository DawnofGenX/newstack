--  The only unit that touches real argv and the real output streams.
with Ada.Command_Line;
with Ada.Strings.Unbounded;

with Textstat.Options;
with Textstat.Output;
with Textstat.Runner;

procedure Main is
   use Ada.Strings.Unbounded;

   Count  : constant Natural := Ada.Command_Line.Argument_Count;
   Args   : Textstat.Options.Arg_Array (1 .. Count);
   Status : Integer;
begin
   for I in 1 .. Count loop
      Args (I) := To_Unbounded_String (Ada.Command_Line.Argument (I));
   end loop;
   Status := Textstat.Runner.Run
     (Args, Textstat.Output.Write_Out'Access, Textstat.Output.Write_Err'Access);
   Ada.Command_Line.Set_Exit_Status (Ada.Command_Line.Exit_Status (Status));
end Main;

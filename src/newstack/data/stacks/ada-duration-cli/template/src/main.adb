with Ada.Command_Line;
with Ada.Integer_Text_IO;
with Ada.Text_IO;

with Durations;

procedure Main is
   use Ada.Command_Line;
   use Durations;

   procedure Usage is
   begin
      Ada.Text_IO.Put_Line ("Usage: {{ npm_name }} parse DURATION");
      Ada.Text_IO.Put_Line ("       {{ npm_name }} format SECONDS");
      Ada.Text_IO.Put_Line ("       {{ npm_name }} human DURATION");
      Ada.Text_IO.Put_Line ("Parse and format ISO-8601 or human durations.");
   end Usage;

   function To_Integer (Text : String; Ok : out Boolean) return Long_Long_Integer is
      Value : Long_Long_Integer := 0;
      I : Positive := Text'First;
      Negative : Boolean := False;
   begin
      Ok := False;
      if Text'Length = 0 then return 0; end if;
      if Text (Text'First) = '-' then
         Negative := True;
         I := I + 1;
      end if;
      if I > Text'Last then return 0; end if;
      while I <= Text'Last loop
         if Text (I) not in '0' .. '9' then
            return 0;
         end if;
         Value := Value * 10 + Character'Pos (Text (I)) - Character'Pos ('0');
         I := I + 1;
      end loop;
      Ok := True;
      if Negative then return -Value; end if;
      return Value;
   end To_Integer;

begin
   if Argument_Count = 0 or else Argument (1) = "--help" or else Argument (1) = "-h" then
      Usage;
      return;
   end if;
   if Argument (1) = "--version" then
      Ada.Text_IO.Put_Line ("0.1.0");
      return;
   end if;

   if Argument (1) = "parse" then
      if Argument_Count < 2 then Usage; Set_Exit_Status (2); return; end if;
      declare
         Ok : Boolean;
         V  : constant Seconds := Parse (Argument (2), Ok);
      begin
         if not Ok then
            Ada.Text_IO.Put_Line (Ada.Text_IO.Standard_Error, "invalid duration: " & Argument (2));
            Set_Exit_Status (1);
            return;
         end if;
         Ada.Integer_Text_IO.Put (Integer (V), Width => 0);
         Ada.Text_IO.New_Line;
      end;
   elsif Argument (1) = "format" then
      if Argument_Count < 2 then Usage; Set_Exit_Status (2); return; end if;
      declare
         Ok : Boolean;
         V  : constant Long_Long_Integer := To_Integer (Argument (2), Ok);
      begin
         if not Ok then
            Ada.Text_IO.Put_Line (Ada.Text_IO.Standard_Error, "invalid seconds: " & Argument (2));
            Set_Exit_Status (2);
            return;
         end if;
         Ada.Text_IO.Put_Line (Format_Iso (Seconds (V)));
      end;
   elsif Argument (1) = "human" then
      if Argument_Count < 2 then Usage; Set_Exit_Status (2); return; end if;
      declare
         Ok : Boolean;
         V  : constant Long_Long_Integer := To_Integer (Argument (2), Ok);
      begin
         if not Ok then
            Ada.Text_IO.Put_Line (Ada.Text_IO.Standard_Error, "invalid seconds: " & Argument (2));
            Set_Exit_Status (2);
            return;
         end if;
         Ada.Text_IO.Put_Line (Format_Human (Seconds (V)));
      end;
   elsif Argument (1)'Length > 0 and then Argument (1) (Argument (1)'First) = '-' then
      Usage;
      Set_Exit_Status (2);
   else
      --  Allow `duration "PT..."` as parse shorthand.
      declare
         Ok : Boolean;
         V  : constant Seconds := Parse (Argument (1), Ok);
      begin
         if Ok then
            Ada.Integer_Text_IO.Put (Integer (V), Width => 0);
            Ada.Text_IO.New_Line;
         else
            Usage;
            Set_Exit_Status (2);
         end if;
      end;
   end if;
end Main;

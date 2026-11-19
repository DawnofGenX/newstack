with Ada.Text_IO;

with Durations;

procedure Run_Tests is
   use Durations;

   Ok : Boolean;
   V  : Seconds;
begin
   V := Parse ("PT1H30M", Ok);
   if not Ok or else V /= 5400 then
      Ada.Text_IO.Put_Line ("FAIL parse iso");
   else
      Ada.Text_IO.Put_Line ("PASS parse iso");
   end if;

   V := Parse ("1h 30m", Ok);
   if not Ok or else V /= 5400 then
      Ada.Text_IO.Put_Line ("FAIL parse human");
   else
      Ada.Text_IO.Put_Line ("PASS parse human");
   end if;

   if Format_Iso (Seconds (5400)) /= "PT1H30M" then
      Ada.Text_IO.Put_Line ("FAIL format iso: " & Format_Iso (Seconds (5400)));
   else
      Ada.Text_IO.Put_Line ("PASS format iso");
   end if;

   if Format_Human (Seconds (5400)) /= "1h 30m" then
      Ada.Text_IO.Put_Line ("FAIL format human: " & Format_Human (Seconds (5400)));
   else
      Ada.Text_IO.Put_Line ("PASS format human");
   end if;

   V := Parse ("not-a-duration", Ok);
   if Ok then
      Ada.Text_IO.Put_Line ("FAIL invalid accepted");
   else
      Ada.Text_IO.Put_Line ("PASS invalid rejected");
   end if;

   if Format_Iso (Seconds (0)) /= "PT0S" then
      Ada.Text_IO.Put_Line ("FAIL zero iso");
   else
      Ada.Text_IO.Put_Line ("PASS zero iso");
   end if;
end Run_Tests;

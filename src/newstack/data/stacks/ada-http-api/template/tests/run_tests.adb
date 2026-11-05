with Ada.Strings.Unbounded; use Ada.Strings.Unbounded;
with Ada.Text_IO;
with GNAT.OS_Lib;
with Textstat.Contract;

--  A dependency-free check script: every Check() prints FAIL plus its detail
--  when it fails, and the process exits non-zero if any of them failed.
procedure Run_Tests is

   Failed : Natural := 0;
   Passed : Natural := 0;

   function Trim (Text : String) return String is
      First : Natural := Text'First;
      Last  : Natural := Text'Last;
   begin
      while First <= Last and then Text (First) = ' ' loop
         First := First + 1;
      end loop;
      while Last >= First and then Text (Last) = ' ' loop
         Last := Last - 1;
      end loop;
      return Text (First .. Last);
   end Trim;

   function Contains (Text : String; Pattern : String) return Boolean is
   begin
      if Pattern'Length = 0 or else Text'Length < Pattern'Length then
         return False;
      end if;
      for Index in Text'First .. Text'Last - Pattern'Length + 1 loop
         if Text (Index .. Index + Pattern'Length - 1) = Pattern then
            return True;
         end if;
      end loop;
      return False;
   end Contains;

   procedure Check (Name : String; Ok : Boolean; Detail : String := "") is
   begin
      if Ok then
         Passed := Passed + 1;
      else
         Failed := Failed + 1;
         Ada.Text_IO.Put_Line
           ("FAIL " & Name & (if Detail'Length > 0 then " -> " & Detail else ""));
      end if;
   end Check;

   function Route (Method : String; Path : String; Query : String; Expected : String)
     return Textstat.Contract.Reply renames Textstat.Contract.Route;

   procedure Expect (Name : String; Status : Natural; Expected : String;
                     Method : String; Path : String;
                     Query : String := ""; Text : String := "") is
      Got : constant Textstat.Contract.Reply := Route (Method, Path, Query, Text);
   begin
      Check (Name & " status", Got.Status = Status, Trim (Natural'Image (Got.Status)));
      Check (Name & " body", To_String (Got.Payload) = Expected, To_String (Got.Payload));
   end Expect;

   --  Counted answers are checked field by field, so the test does not depend
   --  on the key order the reply happens to use.
   procedure Expect_Counts
     (Name : String; Method : String; Path : String; Query : String := "";
      Text : String := ""; Line : Natural; Word : Natural; Byte : Natural)
   is
      Got  : constant Textstat.Contract.Reply := Route (Method, Path, Query, Text);
      Expected : constant String := To_String (Got.Payload);
   begin
      Check (Name & " status", Got.Status = 200, Trim (Natural'Image (Got.Status)));
      Check (Name & " lines",
             Contains (Expected, """lines"":" & Trim (Natural'Image (Line))), Expected);
      Check (Name & " words",
             Contains (Expected, """words"":" & Trim (Natural'Image (Word))), Expected);
      Check (Name & " bytes",
             Contains (Expected, """bytes"":" & Trim (Natural'Image (Byte))), Expected);
   end Expect_Counts;

begin
   --  health
   Expect ("health", 200, "{""status"":""ok""}", "GET", "/health");

   --  GET /stats
   Expect_Counts ("get empty", "GET", "/stats", Query => "text=",
                  Line => 0, Word => 0, Byte => 0);
   Expect_Counts ("get hello", "GET", "/stats", Query => "text=hello%20world%0A",
                  Line => 1, Word => 2, Byte => 12);
   Expect_Counts ("get utf8", "GET", "/stats",
                  Query => "text=h%C3%A9llo%20w%C3%B6rld%0A",
                  Line => 1, Word => 2, Byte => 14);
   Expect ("get without text", 422, "{""error"":""missing_text""}", "GET", "/stats");

   --  POST /stats
   Expect_Counts ("post hello", "POST", "/stats",
                  Text => "{""text"":""a b\nc\n""}", Line => 2, Word => 3, Byte => 6);
   Expect_Counts ("post escaped utf8", "POST", "/stats",
                  Text => "{""text"":""h\u00e9llo""}", Line => 0, Word => 1, Byte => 6);
   Expect ("post without text", 422, "{""error"":""missing_text""}", "POST", "/stats",
           Text => "{}");
   Expect ("post number", 422, "{""error"":""missing_text""}", "POST", "/stats",
           Text => "{""text"":42}");
   Expect ("post broken", 422, "{""error"":""invalid_json""}", "POST", "/stats",
           Text => "nope");

   --  the rest of the contract
   Expect ("unknown route", 404,
           "{""error"":""not_found"",""detail"":""no route for GET /nope""}",
           "GET", "/nope");
   Expect ("wrong method", 405, "{""error"":""method_not_allowed""}", "DELETE", "/health");

   Ada.Text_IO.Put_Line
     ("checks: " & Trim (Natural'Image (Passed + Failed))
      & ", passed: " & Trim (Natural'Image (Passed))
      & ", failed: " & Trim (Natural'Image (Failed)));
   if Failed > 0 then
      GNAT.OS_Lib.OS_Exit (1);
   end if;
end Run_Tests;

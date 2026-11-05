with GNAT.OS_Lib;
with Textstat.Server;

--  Reads HOST (default 127.0.0.1) and PORT (default 8080) from the
--  environment, then serves until the process is killed.
procedure App is

   use type GNAT.OS_Lib.String_Access;

   function Env_Or (Name : String; Fallback : String) return String is
      Value : constant GNAT.OS_Lib.String_Access := GNAT.OS_Lib.Getenv (Name);
   begin
      if Value = null or else Value.all'Length = 0 then
         return Fallback;
      end if;
      return Value.all;
   end Env_Or;

   function Number_Or (Text : String; Fallback : Natural) return Natural is
      Value : Natural := 0;
   begin
      if Text'Length = 0 or else Text'Length > 5 then
         return Fallback;
      end if;
      for Index in Text'Range loop
         if Text (Index) not in '0' .. '9' then
            return Fallback;
         end if;
         Value := Value * 10 + (Character'Pos (Text (Index)) - Character'Pos ('0'));
      end loop;
      if Value = 0 or else Value > 65_535 then
         return Fallback;
      end if;
      return Value;
   end Number_Or;

begin
   Textstat.Server.Serve
     (Env_Or ("HOST", "127.0.0.1"), Number_Or (Env_Or ("PORT", "8080"), 8080));
end App;

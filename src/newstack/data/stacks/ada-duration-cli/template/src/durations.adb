with Ada.Characters.Handling;

package body Durations is

   function Is_Digit (C : Character) return Boolean is
   begin
      return C in '0' .. '9';
   end Is_Digit;

   function Parse_Number (Text : String; I : in out Positive) return Long_Long_Integer is
      Value : Long_Long_Integer := 0;
      Start : constant Positive := I;
   begin
      if I > Text'Last or else not Is_Digit (Text (I)) then
         return 0;
      end if;
      while I <= Text'Last and then Is_Digit (Text (I)) loop
         Value := Value * 10 + Character'Pos (Text (I)) - Character'Pos ('0');
         I := I + 1;
      end loop;
      if I = Start then
         return 0;
      end if;
      return Value;
   end Parse_Number;

   function To_Lower (C : Character) return Character is
   begin
      return Ada.Characters.Handling.To_Lower (C);
   end To_Lower;

   function Parse (Text : String; Ok : out Boolean) return Seconds is
      S : String := Text;
      --  Trim leading/trailing spaces.
      First : Positive := Text'First;
      Last  : Natural := Text'Last;
   begin
      Ok := False;
      while First <= Last and then (Text (First) = ' ' or else Text (First) = ASCII.HT) loop
         First := First + 1;
      end loop;
      while Last >= First and then (Text (Last) = ' ' or else Text (Last) = ASCII.HT) loop
         Last := Last - 1;
      end loop;
      if First > Last then
         return 0;
      end if;
      declare
         T : constant String := Text (First .. Last);
      begin
         if T (T'First) = 'P' or else T (T'First) = 'p' then
            --  ISO-8601 duration.
            declare
               Total : Long_Long_Integer := 0;
               I : Positive := T'First + 1;
               In_Time : Boolean := False;
            begin
               while I <= T'Last loop
                  if T (I) = 'T' or else T (I) = 't' then
                     In_Time := True;
                     I := I + 1;
                  elsif Is_Digit (T (I)) then
                     declare
                        N : constant Long_Long_Integer := Parse_Number (T, I);
                        Unit : Character;
                     begin
                        if I > T'Last then
                           return 0;
                        end if;
                        Unit := To_Lower (T (I));
                        I := I + 1;
                        case Unit is
                           when 'd' => Total := Total + N * 86400;
                           when 'h' => Total := Total + N * 3600;
                           when 'm' => Total := Total + N * 60;
                           when 's' => Total := Total + N;
                           when 'w' => Total := Total + N * 604800;
                           when others => return 0;
                        end case;
                     end;
                  else
                     return 0;
                  end if;
               end loop;
               Ok := True;
               return Seconds (Total);
            end;
         else
            --  Human form: number followed by optional unit.
            declare
               Total : Long_Long_Integer := 0;
               I : Positive := T'First;
            begin
               while I <= T'Last loop
                  while I <= T'Last and then (T (I) = ' ' or else T (I) = ASCII.HT) loop
                     I := I + 1;
                  end loop;
                  exit when I > T'Last;
                  if not Is_Digit (T (I)) then
                     return 0;
                  end if;
                  declare
                     N : constant Long_Long_Integer := Parse_Number (T, I);
                     Unit : Character := 's';
                     Word : String (1 .. 10);
                     Wlen : Natural := 0;
                  begin
                     --  Consume an alphabetic unit, if any.
                     while I <= T'Last and then
                       ((T (I) >= 'a' and then T (I) <= 'z') or else
                        (T (I) >= 'A' and then T (I) <= 'Z')) loop
                        Wlen := Wlen + 1;
                        if Wlen <= 10 then
                           Word (Wlen) := To_Lower (T (I));
                        end if;
                        I := I + 1;
                     end loop;
                     if Wlen > 0 then
                        if Word (1) = 'd' then
                           Unit := 'd';
                        elsif Word (1) = 'h' then
                           Unit := 'h';
                        elsif Word (1) = 'm' then
                           Unit := 'm';
                        elsif Word (1) = 's' then
                           Unit := 's';
                        else
                           return 0;
                        end if;
                     end if;
                     case Unit is
                        when 'd' => Total := Total + N * 86400;
                        when 'h' => Total := Total + N * 3600;
                        when 'm' => Total := Total + N * 60;
                        when 's' => Total := Total + N;
                        when others => return 0;
                     end case;
                  end;
               end loop;
               Ok := True;
               return Seconds (Total);
            end;
         end if;
      end;
   end Parse;

   function Format_Iso (Value : Seconds) return String is
      V : Long_Long_Integer := Long_Long_Integer (Value);
      Days : Long_Long_Integer;
      Hours : Long_Long_Integer;
      Mins : Long_Long_Integer;
      Secs : Long_Long_Integer;
   begin
      Days := V / 86400;
      V := V mod 86400;
      Hours := V / 3600;
      V := V mod 3600;
      Mins := V / 60;
      Secs := V mod 60;
      declare
         Result : String (1 .. 64);
         Pos : Natural := 1;
         procedure Append (S : String) is
         begin
            Result (Pos .. Pos + S'Length - 1) := S;
            Pos := Pos + S'Length;
         end Append;
         function Img (N : Long_Long_Integer) return String is
            Raw : constant String := Long_Long_Integer'Image (N);
         begin
            if Raw (Raw'First) = ' ' then
               return Raw (Raw'First + 1 .. Raw'Last);
            end if;
            return Raw;
         end Img;
      begin
         Append ("P");
         if Days > 0 then
            Append (Img (Days) & "D");
         end if;
         if Hours = 0 and then Mins = 0 and then Secs = 0 and then Days = 0 then
            Append ("T0S");
            return Result (1 .. Pos - 1);
         end if;
         if Hours > 0 or else Mins > 0 or else Secs > 0 then
            Append ("T");
            if Hours > 0 then Append (Img (Hours) & "H"); end if;
            if Mins > 0 then Append (Img (Mins) & "M"); end if;
            if Secs > 0 or else (Hours = 0 and then Mins = 0) then Append (Img (Secs) & "S"); end if;
         end if;
         if Result (2 .. 2) = "T" and then Days = 0 then
            null;
         end if;
         return Result (1 .. Pos - 1);
      end;
   end Format_Iso;

   function Format_Human (Value : Seconds) return String is
      V : Long_Long_Integer := Long_Long_Integer (Value);
      Days : Long_Long_Integer;
      Hours : Long_Long_Integer;
      Mins : Long_Long_Integer;
      Secs : Long_Long_Integer;
   begin
      Days := V / 86400;
      V := V mod 86400;
      Hours := V / 3600;
      V := V mod 3600;
      Mins := V / 60;
      Secs := V mod 60;
      declare
         Result : String (1 .. 64);
         Pos : Natural := 1;
         procedure Append (S : String) is
         begin
            if Pos > 1 then
               Result (Pos) := ' ';
               Pos := Pos + 1;
            end if;
            Result (Pos .. Pos + S'Length - 1) := S;
            Pos := Pos + S'Length;
         end Append;
         function Img (N : Long_Long_Integer) return String is
            Raw : constant String := Long_Long_Integer'Image (N);
         begin
            if Raw (Raw'First) = ' ' then
               return Raw (Raw'First + 1 .. Raw'Last);
            end if;
            return Raw;
         end Img;
      begin
         if Days > 0 then Append (Img (Days) & "d"); end if;
         if Hours > 0 then Append (Img (Hours) & "h"); end if;
         if Mins > 0 then Append (Img (Mins) & "m"); end if;
         if Secs > 0 or else (Days = 0 and then Hours = 0 and then Mins = 0) then
            Append (Img (Secs) & "s");
         end if;
         return Result (1 .. Pos - 1);
      end;
   end Format_Human;

end Durations;

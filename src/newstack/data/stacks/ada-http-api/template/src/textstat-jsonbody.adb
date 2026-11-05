with Ada.Strings.Unbounded; use Ada.Strings.Unbounded;

package body Textstat.JsonBody is

   Parse_Error : exception;

   Found_Text   : Boolean := False;
   Not_A_String : Boolean := False;
   Captured     : Unbounded_String;

   procedure Skip_Space (Payload : String; Pos : in out Natural) is
   begin
      while Pos <= Payload'Last
        and then (Payload (Pos) = ' '
                  or else Payload (Pos) = ASCII.HT
                  or else Payload (Pos) = ASCII.LF
                  or else Payload (Pos) = ASCII.CR)
      loop
         Pos := Pos + 1;
      end loop;
   end Skip_Space;

   procedure Expect (Payload : String; Pos : in out Natural; Item : Character) is
   begin
      if Pos > Payload'Last or else Payload (Pos) /= Item then
         raise Parse_Error;
      end if;
      Pos := Pos + 1;
   end Expect;

   function Hex_Value (Item : Character) return Natural is
   begin
      case Item is
         when '0' .. '9' => return Character'Pos (Item) - Character'Pos ('0');
         when 'a' .. 'f' => return Character'Pos (Item) - Character'Pos ('a') + 10;
         when 'A' .. 'F' => return Character'Pos (Item) - Character'Pos ('A') + 10;
         when others     => raise Parse_Error;
      end case;
   end Hex_Value;

   function Read_Hex4 (Payload : String; Pos : in out Natural) return Natural is
      Value : Natural := 0;
   begin
      for Count in 1 .. 4 loop
         if Pos > Payload'Last then
            raise Parse_Error;
         end if;
         Value := Value * 16 + Hex_Value (Payload (Pos));
         Pos := Pos + 1;
      end loop;
      return Value;
   end Read_Hex4;

   procedure Append_Utf8 (Target : in out Unbounded_String; Code : Natural) is
   begin
      if Code < 16#80# then
         Append (Target, Character'Val (Code));
      elsif Code < 16#800# then
         Append (Target, Character'Val (16#C0# + Code / 64));
         Append (Target, Character'Val (16#80# + Code mod 64));
      elsif Code < 16#10000# then
         Append (Target, Character'Val (16#E0# + Code / 4096));
         Append (Target, Character'Val (16#80# + (Code / 64) mod 64));
         Append (Target, Character'Val (16#80# + Code mod 64));
      else
         Append (Target, Character'Val (16#F0# + Code / 262144));
         Append (Target, Character'Val (16#80# + (Code / 4096) mod 64));
         Append (Target, Character'Val (16#80# + (Code / 64) mod 64));
         Append (Target, Character'Val (16#80# + Code mod 64));
      end if;
   end Append_Utf8;

   --  Decodes a JSON string starting at the opening quote. Escapes come out as
   --  UTF-8 so "h\u00e9llo" and "h<C3><A9>llo" produce the same bytes.
   function Parse_String (Payload : String; Pos : in out Natural) return String is
      Buffer : Unbounded_String;
   begin
      Expect (Payload, Pos, '"');
      loop
         if Pos > Payload'Last then
            raise Parse_Error;
         end if;
         declare
            Item     : constant Character := Payload (Pos);
            Advanced : Boolean := False;
         begin
            if Item = '"' then
               Pos := Pos + 1;
               exit;
            elsif Item = '\' then
               Pos := Pos + 1;
               if Pos > Payload'Last then
                  raise Parse_Error;
               end if;
               case Payload (Pos) is
                  when '"'  => Append (Buffer, '"');
                  when '\'  => Append (Buffer, '\');
                  when '/'  => Append (Buffer, '/');
                  when 'b'  => Append (Buffer, Character'Val (8));
                  when 'f'  => Append (Buffer, Character'Val (12));
                  when 'n'  => Append (Buffer, ASCII.LF);
                  when 'r'  => Append (Buffer, ASCII.CR);
                  when 't'  => Append (Buffer, ASCII.HT);
                  when 'u'  =>
                     Pos := Pos + 1;
                     declare
                        Code : Natural := Read_Hex4 (Payload, Pos);
                     begin
                        if Code in 16#D800# .. 16#DBFF# then
                           --  A surrogate pair only means something with its
                           --  low half, which must follow immediately.
                           Expect (Payload, Pos, '\');
                           Expect (Payload, Pos, 'u');
                           declare
                              Low : constant Natural := Read_Hex4 (Payload, Pos);
                           begin
                              if Low not in 16#DC00# .. 16#DFFF# then
                                 raise Parse_Error;
                              end if;
                              Code := 16#10000#
                                + (Code - 16#D800#) * 1024
                                + (Low - 16#DC00#);
                           end;
                        elsif Code in 16#DC00# .. 16#DFFF# then
                           raise Parse_Error;
                        end if;
                        Append_Utf8 (Buffer, Code);
                     end;
                     Advanced := True;
                  when others =>
                     raise Parse_Error;
               end case;
               if not Advanced then
                  Pos := Pos + 1;
               end if;
            else
               Append (Buffer, Item);
               Pos := Pos + 1;
            end if;
         end;
      end loop;
      return To_String (Buffer);
   end Parse_String;

   procedure Skip_Number (Payload : String; Pos : in out Natural) is
   begin
      if Pos <= Payload'Last and then Payload (Pos) = '-' then
         Pos := Pos + 1;
      end if;
      if Pos > Payload'Last or else Payload (Pos) not in '0' .. '9' then
         raise Parse_Error;
      end if;
      while Pos <= Payload'Last and then Payload (Pos) in '0' .. '9' loop
         Pos := Pos + 1;
      end loop;
      if Pos <= Payload'Last and then Payload (Pos) = '.' then
         Pos := Pos + 1;
         if Pos > Payload'Last or else Payload (Pos) not in '0' .. '9' then
            raise Parse_Error;
         end if;
         while Pos <= Payload'Last and then Payload (Pos) in '0' .. '9' loop
            Pos := Pos + 1;
         end loop;
      end if;
      if Pos <= Payload'Last and then (Payload (Pos) = 'e' or else Payload (Pos) = 'E') then
         Pos := Pos + 1;
         if Pos <= Payload'Last and then (Payload (Pos) = '+' or else Payload (Pos) = '-') then
            Pos := Pos + 1;
         end if;
         if Pos > Payload'Last or else Payload (Pos) not in '0' .. '9' then
            raise Parse_Error;
         end if;
         while Pos <= Payload'Last and then Payload (Pos) in '0' .. '9' loop
            Pos := Pos + 1;
         end loop;
      end if;
   end Skip_Number;

   procedure Skip_Value (Payload : String; Pos : in out Natural);

   procedure Skip_Object (Payload : String; Pos : in out Natural; Capture : Boolean) is
      Name : Unbounded_String;
   begin
      Expect (Payload, Pos, '{');
      Skip_Space (Payload, Pos);
      if Pos <= Payload'Last and then Payload (Pos) = '}' then
         Pos := Pos + 1;
         return;
      end if;
      loop
         Skip_Space (Payload, Pos);
         Name := To_Unbounded_String (Parse_String (Payload, Pos));
         Skip_Space (Payload, Pos);
         Expect (Payload, Pos, ':');
         Skip_Space (Payload, Pos);
         if Capture and then To_String (Name) = "text" then
            if Pos > Payload'Last or else Payload (Pos) /= '"' then
               --  Present but not a string: remember that it was seen without
               --  treating the body as broken.
               Found_Text := True;
               Not_A_String := True;
               Skip_Value (Payload, Pos);
            else
               Found_Text := True;
               Captured := To_Unbounded_String (Parse_String (Payload, Pos));
            end if;
         else
            Skip_Value (Payload, Pos);
         end if;
         Skip_Space (Payload, Pos);
         if Pos <= Payload'Last and then Payload (Pos) = ',' then
            Pos := Pos + 1;
         else
            Expect (Payload, Pos, '}');
            return;
         end if;
      end loop;
   end Skip_Object;

   procedure Skip_Array (Payload : String; Pos : in out Natural) is
   begin
      Expect (Payload, Pos, '[');
      Skip_Space (Payload, Pos);
      if Pos <= Payload'Last and then Payload (Pos) = ']' then
         Pos := Pos + 1;
         return;
      end if;
      loop
         Skip_Space (Payload, Pos);
         Skip_Value (Payload, Pos);
         Skip_Space (Payload, Pos);
         if Pos <= Payload'Last and then Payload (Pos) = ',' then
            Pos := Pos + 1;
         else
            Expect (Payload, Pos, ']');
            return;
         end if;
      end loop;
   end Skip_Array;

   procedure Skip_Value (Payload : String; Pos : in out Natural) is
   begin
      if Pos > Payload'Last then
         raise Parse_Error;
      end if;
      case Payload (Pos) is
         when '"' =>
            declare
               Ignored : constant String := Parse_String (Payload, Pos);
               pragma Unreferenced (Ignored);
            begin
               null;
            end;
         when '{' =>
            Skip_Object (Payload, Pos, False);
         when '[' =>
            Skip_Array (Payload, Pos);
         when 't' =>
            if Pos + 3 > Payload'Last or else Payload (Pos .. Pos + 3) /= "true" then
               raise Parse_Error;
            end if;
            Pos := Pos + 4;
         when 'f' =>
            if Pos + 4 > Payload'Last or else Payload (Pos .. Pos + 4) /= "false" then
               raise Parse_Error;
            end if;
            Pos := Pos + 5;
         when 'n' =>
            if Pos + 3 > Payload'Last or else Payload (Pos .. Pos + 3) /= "null" then
               raise Parse_Error;
            end if;
            Pos := Pos + 4;
         when others =>
            Skip_Number (Payload, Pos);
      end case;
   end Skip_Value;

   function Read_Text_Body
     (Payload  : String;
      Value : out Ada.Strings.Unbounded.Unbounded_String) return Text_Kind
   is
      Position : Natural := Payload'First;
   begin
      Found_Text := False;
      Not_A_String := False;
      Captured := Null_Unbounded_String;
      Value := Null_Unbounded_String;
      begin
         Skip_Space (Payload, Position);
         if Position > Payload'Last or else Payload (Position) /= '{' then
            raise Parse_Error;
         end if;
         Skip_Object (Payload, Position, True);
         Skip_Space (Payload, Position);
         if Position <= Payload'Last then
            raise Parse_Error;
         end if;
      exception
         when Parse_Error =>
            return Invalid;
      end;
      if not Found_Text or else Not_A_String then
         return Missing;
      end if;
      Value := Captured;
      return Text;
   end Read_Text_Body;

end Textstat.JsonBody;

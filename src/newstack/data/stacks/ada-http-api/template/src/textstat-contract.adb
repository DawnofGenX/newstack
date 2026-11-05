with Ada.Strings.Unbounded; use Ada.Strings.Unbounded;
with Textstat.Counts;
with Textstat.JsonBody;

package body Textstat.Contract is

   Backslash : constant Character := '\';

   function Image_Of (Value : Natural) return String is
      Raw : constant String := Natural'Image (Value);
   begin
      return Raw (Raw'First + 1 .. Raw'Last);
   end Image_Of;

   function Hex_Digit (Value : Natural) return Character is
      Alphabet : constant String := "0123456789abcdef";
   begin
      return Alphabet (Alphabet'First + Value);
   end Hex_Digit;

   --  Ada has no escape sequences, so a backslash is appended as its own
   --  character rather than written inside a literal.
   function Quote (Text : String) return String is
      Buffer : Unbounded_String;
   begin
      Append (Buffer, '"');
      for Index in Text'Range loop
         declare
            Item : constant Character := Text (Index);
            Code : constant Natural := Character'Pos (Item);
         begin
            case Item is
               when '"' =>
                  Append (Buffer, Backslash);
                  Append (Buffer, '"');
               when '\' =>
                  Append (Buffer, Backslash);
                  Append (Buffer, Backslash);
               when ASCII.LF =>
                  Append (Buffer, Backslash);
                  Append (Buffer, 'n');
               when ASCII.CR =>
                  Append (Buffer, Backslash);
                  Append (Buffer, 'r');
               when ASCII.HT =>
                  Append (Buffer, Backslash);
                  Append (Buffer, 't');
               when others =>
                  if Code < 16#20# then
                     Append (Buffer, Backslash);
                     Append (Buffer, 'u');
                     Append (Buffer, '0');
                     Append (Buffer, '0');
                     Append (Buffer, Hex_Digit (Code / 16));
                     Append (Buffer, Hex_Digit (Code mod 16));
                  else
                     Append (Buffer, Item);
                  end if;
            end case;
         end;
      end loop;
      Append (Buffer, '"');
      return To_String (Buffer);
   end Quote;

   function Counts_Json (Text : String; Counted : Textstat.Counts.Counts) return String is
   begin
      return "{""text"":" & Quote (Text)
        & ",""lines"":" & Image_Of (Counted.Lines)
        & ",""words"":" & Image_Of (Counted.Words)
        & ",""bytes"":" & Image_Of (Counted.Bytes) & "}";
   end Counts_Json;

   function Error (Status : Natural; Code : String) return Reply is
   begin
      return (Status, To_Unbounded_String ("{""error"":" & Quote (Code) & "}"));
   end Error;

   function Error_Detail
     (Status : Natural;
      Code   : String;
      Detail : String) return Reply is
   begin
      return (Status,
              To_Unbounded_String
                ("{""error"":" & Quote (Code)
                 & ",""detail"":" & Quote (Detail) & "}"));
   end Error_Detail;

   function Percent_Decode (Raw : String) return String is
      Buffer : Unbounded_String;

      function Value_Of (Item : Character) return Natural is
      begin
         case Item is
            when '0' .. '9' => return Character'Pos (Item) - Character'Pos ('0');
            when 'a' .. 'f' => return Character'Pos (Item) - Character'Pos ('a') + 10;
            when 'A' .. 'F' => return Character'Pos (Item) - Character'Pos ('A') + 10;
            when others     => return 16;
         end case;
      end Value_Of;

      Position : Natural := Raw'First;
   begin
      while Position <= Raw'Last loop
         if Raw (Position) = '%' and then Position + 2 <= Raw'Last
           and then Value_Of (Raw (Position + 1)) < 16
           and then Value_Of (Raw (Position + 2)) < 16
         then
            Append (Buffer,
                    Character'Val (Value_Of (Raw (Position + 1)) * 16
                                   + Value_Of (Raw (Position + 2))));
            Position := Position + 3;
         elsif Raw (Position) = '+' then
            Append (Buffer, ' ');
            Position := Position + 1;
         else
            Append (Buffer, Raw (Position));
            Position := Position + 1;
         end if;
      end loop;
      return To_String (Buffer);
   end Percent_Decode;

   --  True when Name appears in Query, which arrives without its leading "?"
   --  and with "+" and "%XX" still encoded.
   function Query_Param
     (Query : String;
      Name  : String;
      Value : out Unbounded_String) return Boolean
   is
      Start : Natural := Query'First;
      Stop  : Natural;
   begin
      Value := Null_Unbounded_String;
      if Query'Length = 0 then
         return False;
      end if;
      loop
         Stop := Start;
         while Stop <= Query'Last and then Query (Stop) /= '&' loop
            Stop := Stop + 1;
         end loop;
         declare
            Pair  : constant String := Query (Start .. Stop - 1);
            Split : Natural := Pair'First;
         begin
            while Split <= Pair'Last and then Pair (Split) /= '=' loop
               Split := Split + 1;
            end loop;
            if Split <= Pair'Last then
               if Percent_Decode (Pair (Pair'First .. Split - 1)) = Name then
                  Value := To_Unbounded_String
                    (Percent_Decode (Pair (Split + 1 .. Pair'Last)));
                  return True;
               end if;
            elsif Percent_Decode (Pair) = Name then
               --  A bare "text" with no "=" is still the field, with no value.
               Value := Null_Unbounded_String;
               return True;
            end if;
         end;
         exit when Stop > Query'Last;
         Start := Stop + 1;
      end loop;
      return False;
   end Query_Param;

   function Route
     (Method : String;
      Path   : String;
      Query  : String;
      Payload   : String) return Reply
   is
      Counted  : Textstat.Counts.Counts;
      Text     : Unbounded_String;
      Has_Text : Boolean;
   begin
      if Path = "/health" then
         if Method = "GET" then
            return (200, To_Unbounded_String ("{""status"":""ok""}"));
         end if;
         return Error (405, "method_not_allowed");
      elsif Path = "/stats" then
         if Method = "GET" then
            Has_Text := Query_Param (Query, "text", Text);
            if not Has_Text then
               return Error (422, "missing_text");
            end if;
            Counted := Textstat.Counts.Count_Text (To_String (Text));
            return (200, To_Unbounded_String (Counts_Json (To_String (Text), Counted)));
         elsif Method = "POST" then
            case Textstat.JsonBody.Read_Text_Body (Payload, Text) is
               when Textstat.JsonBody.Invalid =>
                  return Error (422, "invalid_json");
               when Textstat.JsonBody.Missing =>
                  return Error (422, "missing_text");
               when Textstat.JsonBody.Text =>
                  Counted := Textstat.Counts.Count_Text (To_String (Text));
                  return (200, To_Unbounded_String (Counts_Json (To_String (Text), Counted)));
            end case;
         end if;
         return Error (405, "method_not_allowed");
      end if;
      return Error_Detail (404, "not_found", "no route for " & Method & " " & Path);
   end Route;

end Textstat.Contract;

with Ada.Characters.Handling;
with Ada.Streams; use Ada.Streams;
with Ada.Strings.Unbounded; use Ada.Strings.Unbounded;
with Ada.Text_IO;
with GNAT.Sockets;
with Textstat.Contract;

package body Textstat.Server is

   package Sockets renames GNAT.Sockets;

   Max_Header : constant := 8_192;
   Max_Body   : constant := 65_536;
   Max_Read   : constant := 4_096;

   function Image_Of (Value : Natural) return String is
      Raw : constant String := Natural'Image (Value);
   begin
      return Raw (Raw'First + 1 .. Raw'Last);
   end Image_Of;

   --  GNAT.Sockets speaks bytes, not characters, so these two are the only
   --  places that know about the encoding (one byte per character here).
   function Text_Of (Data : Stream_Element_Array) return String is
      Result : String (1 .. Data'Length);
   begin
      for Index in Result'Range loop
         Result (Index) :=
           Character'Val (Data (Data'First + Stream_Element_Offset (Index - 1)));
      end loop;
      return Result;
   end Text_Of;

   function Bytes_Of (Text : String) return Stream_Element_Array is
      Result : Stream_Element_Array (1 .. Text'Length);
   begin
      for Index in Text'Range loop
         Result (Stream_Element_Offset (Index - Text'First + 1)) :=
           Stream_Element (Character'Pos (Text (Index)));
      end loop;
      return Result;
   end Bytes_Of;

   function Reason (Status : Natural) return String is
   begin
      case Status is
         when 200 => return "OK";
         when 404 => return "Not Found";
         when 405 => return "Method Not Allowed";
         when 413 => return "Payload Too Large";
         when 422 => return "Unprocessable Entity";
         when others => return "Internal Server Error";
      end case;
   end Reason;

   --  Reads until the blank line that ends the header block. Bytes past that
   --  line are body bytes the caller must not read twice, so they come back
   --  in Extra.
   procedure Read_Header
     (Client : Sockets.Socket_Type;
      Head   : out Unbounded_String;
      Extra  : out Unbounded_String)
   is
      Buffer : Stream_Element_Array (1 .. Max_Read);
      Last   : Stream_Element_Offset;
   begin
      Head := Null_Unbounded_String;
      Extra := Null_Unbounded_String;
      loop
         Sockets.Receive_Socket (Client, Buffer, Last);
         if Last < Buffer'First then
            Head := Null_Unbounded_String;
            return;
         end if;
         Append (Head, Text_Of (Buffer (Buffer'First .. Last)));
         declare
            Text : constant String := To_String (Head);
         begin
            if Text'Length >= 4 then
               for Index in Text'First .. Text'Last - 3 loop
                  if Text (Index) = ASCII.CR
                    and then Text (Index + 1) = ASCII.LF
                    and then Text (Index + 2) = ASCII.CR
                    and then Text (Index + 3) = ASCII.LF
                  then
                     if Index + 4 <= Text'Last then
                        Extra := To_Unbounded_String (Text (Index + 4 .. Text'Last));
                     end if;
                     Head := To_Unbounded_String (Text (Text'First .. Index + 3));
                     return;
                  end if;
               end loop;
            end if;
            if Text'Length > Max_Header then
               Head := Null_Unbounded_String;
               return;
            end if;
         end;
      end loop;
   end Read_Header;

   --  Header names are case-insensitive, so both sides are folded before the
   --  compare: curl sends "Content-Length", everybody else sends something else.
   function Header_Value (Head : String; Name : String) return String is
      Wanted : constant String := Ada.Characters.Handling.To_Lower (Name);
      Start  : Natural := Head'First;
   begin
      while Start <= Head'Last loop
         declare
            Stop : Natural := Start;
         begin
            while Stop <= Head'Last and then Head (Stop) /= ASCII.LF loop
               Stop := Stop + 1;
            end loop;
            declare
               Line  : constant String := Head (Start .. Stop - 1);
               Colon : Natural := Line'First;
            begin
               while Colon <= Line'Last and then Line (Colon) /= ':' loop
                  Colon := Colon + 1;
               end loop;
               if Colon <= Line'Last then
                  declare
                     Field : constant String := Line (Line'First .. Colon - 1);
                     Value : Unbounded_String;
                  begin
                     if Ada.Characters.Handling.To_Lower (Field) = Wanted then
                        for Index in Colon + 1 .. Line'Last loop
                           if Line (Index) /= ' '
                             and then Line (Index) /= ASCII.HT
                             and then Line (Index) /= ASCII.CR
                           then
                              Append (Value, Line (Index));
                           end if;
                        end loop;
                        return To_String (Value);
                     end if;
                  end;
               end if;
            end;
            Start := Stop + 1;
         end;
      end loop;
      return "";
   end Header_Value;

   function Number_Of (Text : String) return Natural is
      Value     : Natural := 0;
      Has_Digit : Boolean := False;
   begin
      for Index in Text'Range loop
         exit when Text (Index) not in '0' .. '9';
         Value := Value * 10 + (Character'Pos (Text (Index)) - Character'Pos ('0'));
         Has_Digit := True;
      end loop;
      if not Has_Digit then
         return 0;
      end if;
      return Value;
   end Number_Of;

   --  "GET /stats?text=a%20b HTTP/1.1" -> method and target.
   procedure Split_Request_Line
     (Head   : String;
      Method : out Unbounded_String;
      Target : out Unbounded_String)
   is
      Stop : Natural := Head'First;
   begin
      Method := Null_Unbounded_String;
      Target := Null_Unbounded_String;
      while Stop <= Head'Last and then Head (Stop) /= ASCII.LF loop
         Stop := Stop + 1;
      end loop;
      declare
         Line  : constant String := Head (Head'First .. Stop - 1);
         Space : Natural := Line'First;
      begin
         while Space <= Line'Last and then Line (Space) /= ' ' loop
            Space := Space + 1;
         end loop;
         if Space > Line'Last then
            return;
         end if;
         Method := To_Unbounded_String (Line (Line'First .. Space - 1));
         declare
            Start : constant Natural := Space + 1;
            After : Natural := Start;
         begin
            while After <= Line'Last and then Line (After) /= ' ' loop
               After := After + 1;
            end loop;
            if After > Start then
               Target := To_Unbounded_String (Line (Start .. After - 1));
            end if;
         end;
      end;
   end Split_Request_Line;

   procedure Send_Response
     (Client  : Sockets.Socket_Type;
      Status  : Natural;
      Payload : String)
   is
      Head : constant String :=
        "HTTP/1.1 " & Image_Of (Status) & " " & Reason (Status) & ASCII.CR & ASCII.LF
        & "content-type: application/json" & ASCII.CR & ASCII.LF
        & "content-length: " & Image_Of (Payload'Length) & ASCII.CR & ASCII.LF
        & "connection: close" & ASCII.CR & ASCII.LF
        & ASCII.CR & ASCII.LF;
      Last : Stream_Element_Offset;
   begin
      Sockets.Send_Socket (Client, Bytes_Of (Head & Payload), Last);
   end Send_Response;

   procedure Handle (Client : Sockets.Socket_Type) is
      Head   : Unbounded_String;
      Extra  : Unbounded_String;
      Content   : Unbounded_String;
      Wanted : Natural;
      Buffer : Stream_Element_Array (1 .. Max_Read);
      Last   : Stream_Element_Offset;
   begin
      Read_Header (Client, Head, Extra);
      if Length (Head) = 0 then
         Send_Response (Client, 422, "{""error"":""bad_request""}");
         return;
      end if;
      Wanted := Number_Of (Header_Value (To_String (Head), "content-length"));
      if Wanted > Max_Body then
         Send_Response (Client, 413, "{""error"":""body_too_large""}");
         return;
      end if;
      Content := Extra;
      while Length (Content) < Wanted loop
         Sockets.Receive_Socket (Client, Buffer, Last);
         exit when Last < Buffer'First;
         Append (Content, Text_Of (Buffer (Buffer'First .. Last)));
      end loop;
      if Length (Content) > Wanted then
         Content := To_Unbounded_String (Slice (Content, 1, Wanted));
      end if;
      declare
         Method : Unbounded_String;
         Target : Unbounded_String;
         Path   : Unbounded_String;
         Query  : Unbounded_String;
         Reply  : Textstat.Contract.Reply;
      begin
         Split_Request_Line (To_String (Head), Method, Target);
         declare
            Raw   : constant String := To_String (Target);
            Split : Natural := Raw'First;
         begin
            while Split <= Raw'Last and then Raw (Split) /= '?' loop
               Split := Split + 1;
            end loop;
            if Split > Raw'Last then
               Path := To_Unbounded_String (Raw);
            else
               Path := To_Unbounded_String (Raw (Raw'First .. Split - 1));
               if Split < Raw'Last then
                  Query := To_Unbounded_String (Raw (Split + 1 .. Raw'Last));
               end if;
            end if;
         end;
         Reply := Textstat.Contract.Route
           (To_String (Method), To_String (Path), To_String (Query), To_String (Content));
         Send_Response (Client, Reply.Status, To_String (Reply.Payload));
      end;
   end Handle;

   procedure Serve (Host : String; Port : Natural) is
      Server  : Sockets.Socket_Type;
      Client  : Sockets.Socket_Type;
      Address : Sockets.Sock_Addr_Type;
   begin
      Sockets.Create_Socket (Server);
      Sockets.Set_Socket_Option
        (Server, Sockets.Socket_Level, (Sockets.Reuse_Address, True));
      Address :=
        (Family => Sockets.Family_Inet,
         Addr   => Sockets.Inet_Addr (Host),
         Port   => Sockets.Port_Type (Port));
      Sockets.Bind_Socket (Server, Address);
      Sockets.Listen_Socket (Server, 16);
      Ada.Text_IO.Put_Line ("listening on http://" & Host & ":" & Image_Of (Port));
      Ada.Text_IO.Flush;
      loop
         Sockets.Accept_Socket (Server, Client, Address);
         begin
            Handle (Client);
         exception
            when others =>
               null;
         end;
         Sockets.Close_Socket (Client);
      end loop;
   end Serve;

end Textstat.Server;

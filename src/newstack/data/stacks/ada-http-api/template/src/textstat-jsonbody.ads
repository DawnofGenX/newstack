with Ada.Strings.Unbounded;

package Textstat.JsonBody is

   type Text_Kind is (Invalid, Missing, Text);

   --  Reads a JSON object body and returns its "text" member. A number or a
   --  nested object counts as Missing, so {"text": 42} answers a missing text
   --  rather than a bad request; anything that is not one well-formed JSON
   --  value is Invalid.
   function Read_Text_Body
     (Payload  : String;
      Value : out Ada.Strings.Unbounded.Unbounded_String) return Text_Kind;

end Textstat.JsonBody;

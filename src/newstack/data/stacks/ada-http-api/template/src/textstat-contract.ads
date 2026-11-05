with Ada.Strings.Unbounded;

package Textstat.Contract is

   type Reply is record
      Status : Natural := 200;
      Payload   : Ada.Strings.Unbounded.Unbounded_String;
   end record;

   --  One pure function per request: no sockets, no globals, so the tests call
   --  it directly and the listener is only glue.
   function Route
     (Method : String;
      Path   : String;
      Query  : String;
      Payload   : String) return Reply;

   function Quote (Text : String) return String;

end Textstat.Contract;

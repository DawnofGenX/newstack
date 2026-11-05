package Textstat.Server is

   --  Accepts one request per connection, answers it and closes: enough for a
   --  JSON service, and it is what keeps the loop small enough to read.
   procedure Serve (Host : String; Port : Natural);

end Textstat.Server;

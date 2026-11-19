--  Parse and format ISO-8601 and human-readable durations, in seconds.
package Durations is

   type Seconds is new Long_Long_Integer;

   function Parse (Text : String; Ok : out Boolean) return Seconds;
   --  Accepts ISO-8601 (PT1H30M) and human forms (1h 30m, 90s).

   function Format_Iso (Value : Seconds) return String;
   function Format_Human (Value : Seconds) return String;

end Durations;

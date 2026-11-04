--  The program logic. Output goes through a subprogram pointer so the suite can
--  capture it instead of spawning a process; only Main touches the real ones.
with Textstat.Options;

package Textstat.Runner is

   type Writer is access procedure (Text : String);
   --  Writers append one line; they are not given the newline.

   Program : constant String := "{{ npm_name }}";

   function Run (Args : Textstat.Options.Arg_Array;
                 Out_Write, Err_Write : Writer) return Integer;
   --  0 when every operand was counted, 1 when one could not be read, 2 for a
   --  usage error.

end Textstat.Runner;

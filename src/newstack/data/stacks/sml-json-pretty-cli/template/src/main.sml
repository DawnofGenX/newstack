structure Main = struct
  fun main () =
    let
      val program = "{{ npm_name }}"
      val args = CommandLine.arguments ()
      val input =
        case args of
            ["--help"] => (TextIO.output (TextIO.stdOut, "Usage: " ^ program ^ " [FILE]\n");
                           OS.Process.exit OS.Process.success;
                           "")
          | [] => TextIO.inputAll TextIO.stdIn
          | [path] => if path = "-" then TextIO.inputAll TextIO.stdIn
                      else TextIO.inputAll (TextIO.openIn path)
          | _ => (TextIO.output (TextIO.stdErr, "Usage: " ^ program ^ " [FILE]\n");
                  OS.Process.exit OS.Process.failure;
                  "")
    in
      (TextIO.output (TextIO.stdOut, Json.pretty (Json.parse input) ^ "\n");
       OS.Process.exit OS.Process.success)
      handle Json.Parse msg =>
        (TextIO.output (TextIO.stdErr, program ^ ": " ^ msg ^ "\n");
         OS.Process.exit OS.Process.failure)
    end
end
val () = Main.main ()

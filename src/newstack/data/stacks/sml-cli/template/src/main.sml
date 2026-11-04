(* The only file that touches the real process. *)
structure Main = struct
  fun readAllIn path =
    let
      val stream = BinIO.openIn path
      val payload = BinIO.inputAll stream
      val () = BinIO.closeIn stream
    in
      payload
    end

  (* The Basis ships no BinIO.stdIn; /dev/stdin is the portable stand-in. *)
  fun readStdin () = readAllIn "/dev/stdin"

  fun main () =
    let
      val program = "{{ npm_name }}"
      val io : Runner.io = { readFile = readAllIn, readStdin = readStdin }
      val result = Runner.run { program = program, args = CommandLine.arguments (), io = io }
      val () = TextIO.output (TextIO.stdOut, #out result)
      val () = TextIO.output (TextIO.stdErr, #err result)
      val () = TextIO.flushOut TextIO.stdOut
    in
      Posix.Process.exit (Word8.fromInt (#code result))
    end
end

val () = Main.main ()

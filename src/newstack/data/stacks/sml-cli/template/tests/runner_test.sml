structure RunnerTest = struct
  fun payload text = Byte.stringToBytes text

  val files = [("a.txt", payload "alpha beta\ngamma delta\n"),
               ("b.txt", payload "one two three")]

  fun readFile name =
    case List.find (fn (key, _) => key = name) files of
        SOME (_, bytes) => bytes
      | NONE => raise Fail ("missing: " ^ name)

  fun fakeIo stdinText : Runner.io =
    { readFile = readFile, readStdin = fn () => payload stdinText }

  fun report args (io : Runner.io) = Runner.run { program = "textstat", args = args, io = io }

  fun runTests () =
    let
      val single = report ["a.txt"] (fakeIo "")
      val () = Harness.equal ("one file, one row", #out single, " 2  4 23 a.txt\n")
      val () = Harness.equalInt ("one file exits 0", #code single, 0)

      val pair = report ["a.txt", "b.txt"] (fakeIo "")
      val () = Harness.equal ("two files get a total row", #out pair,
                              " 2  4 23 a.txt\n 0  3 13 b.txt\n 2  7 36 total\n")

      val narrow = report ["-w", "a.txt", "b.txt"] (fakeIo "")
      val () = Harness.equal ("-w pads to the byte total's width", #out narrow,
                              " 4 a.txt\n 3 b.txt\n 7 total\n")

      val fromStdin = report [] (fakeIo "alpha beta\ngamma\n")
      val () = Harness.equal ("stdin row is unlabelled", #out fromStdin, "      2       3      17\n")

      val dash = report ["-"] (fakeIo "x y\n")
      val () = Harness.equal ("explicit dash is labelled", #out dash, "      1       2       4 -\n")

      val mixed = report ["a.txt", "-"] (fakeIo "x y\n")
      val () = Harness.equal ("a pipeline operand forces seven columns", #out mixed,
                              "      2       4      23 a.txt\n      1       2       4 -\n"
                              ^ "      3       6      27 total\n")

      val missing = report ["a.txt", "gone.txt"] (fakeIo "")
      val () = Harness.equalInt ("a missing file exits 1", #code missing, 1)
      val () = Harness.equal ("the readable file is still counted", #out missing,
                              " 2  4 23 a.txt\n 2  4 23 total\n")
      val () = Harness.check ("the error names the file", String.isSubstring "gone.txt" (#err missing))

      val help = report ["--help"] (fakeIo "")
      val () = Harness.check ("help exits 0", #code help = 0)
      val () = Harness.check ("help goes to stdout", String.isPrefix "Usage: textstat" (#out help))
      val () = Harness.equal ("help writes nothing to stderr", #err help, "")

      val version = report ["--version"] (fakeIo "")
      val () = Harness.equal ("version is one line", #out version, "textstat 0.1.0\n")

      val usage = report ["--nope"] (fakeIo "")
      val () = Harness.equalInt ("usage errors exit 2", #code usage, 2)
      val () = Harness.equal ("usage errors write nothing to stdout", #out usage, "")
    in
      ()
    end
end

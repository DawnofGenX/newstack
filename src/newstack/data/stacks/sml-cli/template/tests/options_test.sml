structure OptionsTest = struct
  fun run () =
    let
      fun onRun label args test =
        case Options.parse args of
            Options.Run options => Harness.check (label, test options)
          | _ => Harness.check (label ^ " (not a run)", false)

      val () = onRun "no flags means all three figures" []
                    (fn opts => #lines opts andalso #words opts andalso #bytes opts)
      val () = onRun "clustered flags apply both" ["-lw"]
                    (fn opts => #lines opts andalso #words opts andalso not (#bytes opts))
      val () = onRun "long flag" ["--bytes"]
                    (fn opts => #bytes opts andalso not (#lines opts))
      val () = onRun "dash stays an operand" ["-", "b.txt"]
                    (fn opts => #operands opts = ["-", "b.txt"])
      val () = onRun "-- stops option parsing" ["--", "-l"]
                    (fn opts => #operands opts = ["-l"])

      val () = (case Options.parse ["--help"] of
                    Options.Help => Harness.check ("--help asks for help", true)
                  | _ => Harness.check ("--help asks for help", false))
      val () = (case Options.parse ["-h"] of
                    Options.Help => Harness.check ("-h asks for help", true)
                  | _ => Harness.check ("-h asks for help", false))
      val () = (case Options.parse ["--version"] of
                    Options.Version => Harness.check ("--version asks for the version", true)
                  | _ => Harness.check ("--version asks for the version", false))
      val () = (case Options.parse ["--bogus"] of
                    Options.Usage reason =>
                      Harness.check ("unknown long option is a usage error", true)
                  | _ => Harness.check ("unknown long option is a usage error", false))
      val () = (case Options.parse ["-z"] of
                    Options.Usage reason => Harness.check ("unknown short option is a usage error", true)
                  | _ => Harness.check ("unknown short option is a usage error", false))
    in
      ()
    end
end

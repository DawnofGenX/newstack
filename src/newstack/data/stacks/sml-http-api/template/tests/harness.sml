(* A four-word test harness: no framework, no dependency, and a summary line the
   Makefile can trust. *)
structure Harness = struct
  val checks = ref 0
  val failures = ref 0

  fun check (name, ok) =
      let in
        checks := !checks + 1;
        if ok then ()
        else
          (failures := !failures + 1;
           TextIO.output (TextIO.stdErr, "not ok - " ^ name ^ "\n"))
      end

  fun report () =
      let
        val passed = !checks - !failures
      in
        TextIO.output
          (TextIO.stdOut,
           "checks: " ^ Int.toString (!checks)
           ^ ", passed: " ^ Int.toString passed
           ^ ", failed: " ^ Int.toString (!failures) ^ "\n");
        !failures = 0
      end
end

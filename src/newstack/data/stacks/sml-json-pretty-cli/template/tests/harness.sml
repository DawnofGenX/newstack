(* A test harness small enough to read: counters, two assertions, a summary. *)
structure Harness = struct
  val passed = ref 0
  val failed = ref 0

  fun check (label, condition) =
    if condition then
      (passed := !passed + 1; print ("ok   " ^ label ^ "\n"))
    else
      (failed := !failed + 1; print ("FAIL " ^ label ^ "\n"))

  fun equal (label, got : string, want : string) =
    check (if got = want then label
           else label ^ " (got [" ^ got ^ "], want [" ^ want ^ "])",
           got = want)

  fun equalInt (label, got : int, want : int) =
    equal (label, Int.toString got, Int.toString want)

  fun finish () =
    let
      val total = !passed + !failed
      val () = print ("\nchecks: " ^ Int.toString total ^ ", passed: "
                      ^ Int.toString (!passed) ^ ", failed: "
                      ^ Int.toString (!failed) ^ "\n")
    in
      if !failed = 0 then () else OS.Process.exit OS.Process.failure
    end
end

(* Exit non-zero when any check failed, so make and CI see it. *)
val () =
    if Tests.run ()
    then OS.Process.exit OS.Process.success
    else OS.Process.exit OS.Process.failure

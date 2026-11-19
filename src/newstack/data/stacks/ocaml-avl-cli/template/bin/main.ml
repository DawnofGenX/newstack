(* The thin entry point: owns argv, the standard streams and [exit].
 * Everything else lives in the textstat library. *)

let () =
  let args = Array.to_list (Array.sub Sys.argv 1 (Array.length Sys.argv - 1)) in
  exit (Runner.run args stdin stdout stderr)

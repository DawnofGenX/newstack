(* Reads HOST/PORT and serves until killed. *)

let env_or name fallback =
  match Sys.getenv_opt name with
  | Some value when value <> "" -> value
  | _ -> fallback

let () =
  let host = env_or "HOST" "127.0.0.1" in
  let port = int_of_string (env_or "PORT" "8080") in
  Server.serve host port

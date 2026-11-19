(* The only place that understands argv, the standard streams and exit codes.
 *
 * [run] returns the exit code instead of calling [exit], so tests assert the
 * contract without spawning; bin/main.ml turns the value into a process
 * status. *)

open Counts

(* The binary name the user typed. `--help` prints it so the usage line
 * matches the command. *)
let program = "{{ npm_name }}"

(* Read a channel to the end. *)
let read_all ic =
  let buf = Bytes.create 4096 in
  let out = Buffer.create 4096 in
  let rec loop () =
    let n = input ic buf 0 (Bytes.length buf) in
    if n > 0 then (
      Buffer.add_string out (Bytes.to_string (Bytes.sub buf 0 n));
      loop ())
  in
  loop ();
  Buffer.contents out

(* Print the requested figures right-aligned, `wc`-style, then the label. *)
let print_counts (counts : Counts.t) (figures : Options.figures) (label : string) (width : int) (stdout : Out_channel.t) =
  let parts =
    [ if figures.lines then Some counts.lines else None
    ; if figures.words then Some counts.words else None
    ; if figures.bytes then Some counts.bytes else None ]
    |> List.filter_map Fun.id
  in
  let nums = List.map (fun n -> Printf.sprintf "%*d" width n) parts in
  let line =
    match label with
    | "" -> String.concat " " nums
    | _ -> String.concat " " nums ^ " " ^ label
  in
  Printf.fprintf stdout "%s\n" line

(* Run one invocation: 0 success (including `--help`/`--version`),
 * 1 an unreadable file, 2 bad usage. *)
let run (args : string list) (stdin : In_channel.t) (stdout : Out_channel.t) (stderr : Out_channel.t) =
  let parsed = Options.parse args in
  match parsed.status with
  | Options.Help ->
    Printf.fprintf stdout "%s\n" (Options.usage program);
    0
  | Options.Version ->
    Printf.fprintf stdout "%s\n" Options.version;
    0
  | Options.Usage_error ->
    Printf.fprintf stderr "%s\n" ("error: " ^ parsed.message);
    Printf.fprintf stderr "%s\n" "";
    Printf.fprintf stderr "%s\n" (Options.usage program);
    2
  | Options.Ok ->
    (* `""` stands for "no FILE was given": read standard input. *)
    let entries = if parsed.files = [] then [ "" ] else parsed.files in
    let read path =
      if path = "" || path = "-" then Some (read_all stdin)
      else
        (try
           let ic = open_in_bin path in
           let s = read_all ic in
           close_in_noerr ic;
           Some s
         with Sys_error _ -> None)
    in
    let results = List.map (fun path -> (path, read path)) entries in
    let counts = List.filter_map (fun (_, d) -> Option.map of_bytes d) results in
    let total = List.fold_left add empty counts in
    let failed = List.exists (fun (_, d) -> d = None) results in
    (* Right-align every figure to the widest one printed, like `wc`. *)
    let width =
      let digits n = String.length (string_of_int n) in
      List.fold_left
        (fun m c ->
          let m = if parsed.figures.lines then max m (digits c.lines) else m in
          let m = if parsed.figures.words then max m (digits c.words) else m in
          if parsed.figures.bytes then max m (digits c.bytes) else m)
        1 (counts @ [ total ])
    in
    List.iter
      (fun (path, data) ->
        match data with
        | None ->
          Printf.fprintf stderr "%s\n" ("error: cannot open '" ^ path ^ "'");
          ()
        | Some s ->
          let c = of_bytes s in
          print_counts c parsed.figures (if path = "" || path = "-" then "" else path)
            width stdout)
      results;
    if List.length results > 1 then
      print_counts total parsed.figures "total" width stdout;
    if failed then 1 else 0

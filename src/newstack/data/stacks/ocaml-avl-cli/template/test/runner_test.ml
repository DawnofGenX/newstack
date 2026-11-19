(* The exit-code contract, asserted without spawning: [run] returns the code
 * and writes to the channels we hand it.
 *
 * Channels cannot be built over a buffer, so each capture is a temporary file:
 * the test owns the channel, the runner only sees [Out_channel.t]. *)

let capture f =
  let out_path = Filename.temp_file "textstat" ".out" in
  let err_path = Filename.temp_file "textstat" ".err" in
  let oc = open_out_bin out_path in
  let ec = open_out_bin err_path in
  let code = f oc ec in
  close_out_noerr oc;
  close_out_noerr ec;
  let out = In_channel.with_open_bin out_path In_channel.input_all in
  let err = In_channel.with_open_bin err_path In_channel.input_all in
  Sys.remove out_path;
  Sys.remove err_path;
  (code, out, err)

(* A channel over a file with [text] in it, so stdin can be faked the same way
 * stdout is captured. *)
let with_stdin text f =
  let path, oc =
    Filename.open_temp_file ~mode:[Open_wronly; Open_trunc] "textstat" ".in"
  in
  Out_channel.output_string oc text;
  close_out_noerr oc;
  let ic = open_in_bin path in
  let result = f ic in
  close_in_noerr ic;
  Sys.remove path;
  result

let stdin_empty f = with_stdin "" f

let () =

  let code, out, _err = stdin_empty (fun stdin -> capture (fun o e -> Runner.run ["--help"] stdin o e)) in
  Harness.check_eq "help exits 0" 0 code;
  Harness.check_contains "help prints usage" out "usage:";

  let code, out, _ = stdin_empty (fun stdin -> capture (fun o e -> Runner.run ["-V"] stdin o e)) in
  Harness.check_eq "version exits 0" 0 code;
  Harness.check_contains "version prints the version" out "0.1.0";

  let code, _out, err = stdin_empty (fun stdin -> capture (fun o e -> Runner.run ["--bogus"] stdin o e)) in
  Harness.check_eq "unknown flag exits 2" 2 code;
  Harness.check_contains "usage error explains itself" err "unknown option";

  let code, _out, err =
    stdin_empty (fun stdin -> capture (fun o e -> Runner.run ["no-such-file.txt"] stdin o e))
  in
  Harness.check_eq "missing file exits 1" 1 code;
  Harness.check_contains "missing file explains itself" err "cannot open";

  let code, out, _ =
    with_stdin "a b\nc\n" (fun stdin -> capture (fun o e -> Runner.run [] stdin o e))
  in
  Harness.check_eq "stdin exits 0" 0 code;
  Harness.check_contains "stdin counts lines/words/bytes" out "2 3 6";

  let write_temp text =
    let path, oc =
      Filename.open_temp_file ~mode:[Open_wronly; Open_trunc] "textstat" ".txt"
    in
    Out_channel.output_string oc text;
    close_out_noerr oc;
    path
  in

  let f1 = write_temp "one two\nthree\n" in
  let code, out, _ = stdin_empty (fun stdin -> capture (fun o e -> Runner.run [f1] stdin o e)) in
  Harness.check_eq "file exits 0" 0 code;
  (* wc right-aligns to the widest figure: two columns for 14. *)
  Harness.check_contains "file counts lines/words/bytes" out
    (Printf.sprintf "%2d %2d %2d %s" 2 3 14 f1);
  Harness.check_contains "file prints its name" out f1;
  Sys.remove f1;

  let f1 = write_temp "a\n" in
  let f2 = write_temp "b c\n" in
  let code, out, _ = stdin_empty (fun stdin -> capture (fun o e -> Runner.run [f1; f2] stdin o e)) in
  Harness.check_eq "two files exit 0" 0 code;
  Harness.check_contains "two files print a total" out "2 3 6 total";
  Sys.remove f1;
  Sys.remove f2;

  Harness.finish ()

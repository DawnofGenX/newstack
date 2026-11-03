(* Every parser branch: combinable modes, `--`, `-`, help, version, errors. *)

let () =
  let p = Options.parse [] in
  Harness.check_eq "no args: status" (Options.Ok : Options.status) p.status;
  Harness.check "no args: all figures"
    (p.figures.lines && p.figures.words && p.figures.bytes);
  Harness.check_eq "no args: files" [] p.files;

  let p = Options.parse ["-l"] in
  Harness.check_eq "-l: status" (Options.Ok : Options.status) p.status;
  Harness.check "-l: only lines"
    (p.figures.lines && not p.figures.words && not p.figures.bytes);

  let p = Options.parse ["--lines"] in
  Harness.check "--lines: only lines"
    (p.figures.lines && not p.figures.words && not p.figures.bytes);

  let p = Options.parse ["-w"] in
  Harness.check "-w: only words"
    (p.figures.words && not p.figures.lines && not p.figures.bytes);

  let p = Options.parse ["-c"] in
  Harness.check "-c: only bytes"
    (p.figures.bytes && not p.figures.lines && not p.figures.words);

  let p = Options.parse ["-l"; "-w"; "-c"] in
  Harness.check_eq "-l -w -c: status" (Options.Ok : Options.status) p.status;
  Harness.check "-l -w -c: all figures"
    (p.figures.lines && p.figures.words && p.figures.bytes);

  let p = Options.parse ["--help"] in
  Harness.check_eq "--help: status" (Options.Help : Options.status) p.status;

  let p = Options.parse ["-h"] in
  Harness.check_eq "-h: status" (Options.Help : Options.status) p.status;

  let p = Options.parse ["--version"] in
  Harness.check_eq "--version: status" (Options.Version : Options.status) p.status;

  let p = Options.parse ["-V"] in
  Harness.check_eq "-V: status" (Options.Version : Options.status) p.status;

  let p = Options.parse ["--bogus"] in
  Harness.check_eq "--bogus: status" (Options.Usage_error : Options.status) p.status;
  Harness.check_contains "--bogus: message" p.message "unknown option";

  let p = Options.parse ["-x"] in
  Harness.check_eq "-x: status" (Options.Usage_error : Options.status) p.status;

  let p = Options.parse ["--"; "-l"] in
  Harness.check_eq "-- then -l: files" ["-l"] p.files;
  Harness.check_eq "-- then -l: status" (Options.Ok : Options.status) p.status;

  let p = Options.parse ["-"] in
  Harness.check_eq "dash: files" ["-"] p.files;

  let p = Options.parse ["a.txt"; "b.txt"] in
  Harness.check_eq "two files: files" ["a.txt"; "b.txt"] p.files;

  let p = Options.parse ["-l"; "a.txt"] in
  Harness.check "-l file: only lines"
    (p.figures.lines && not p.figures.words && not p.figures.bytes);
  Harness.check_eq "-l file: files" ["a.txt"] p.files;

  Harness.finish ()

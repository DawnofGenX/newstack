(* Command line parsing: argv in, a [parsed] value out. No I/O, no [exit], so
 * every branch is a unit test rather than a subprocess. *)

(* Which figures to print. The flags combine like [wc]: with no counting
 * flag, all three are printed. *)
type figures = {
  lines : bool;
  words : bool;
  bytes : bool;
}

type status = Ok | Help | Version | Usage_error

type parsed = {
  figures : figures;
  files : string list;
  status : status;
  message : string;
}

let all_figures = { lines = true; words = true; bytes = true }
let no_figures = { lines = false; words = false; bytes = false }

let version = "0.1.0"

(* The help text. The caller passes the program name so it matches the
 * binary that is actually running. *)
let usage program =
  "usage: " ^ program ^ " [-l] [-w] [-c] [--] [FILE ...]\n"
  ^ "\n"
  ^ "Count lines, words and bytes in each FILE, or in standard input\n"
  ^ "when no FILE is given. With more than one FILE a total is printed.\n"
  ^ "With no counting flag, all three figures are printed.\n"
  ^ "\n"
  ^ "  -l, --lines     print the line count\n"
  ^ "  -w, --words     print the word count\n"
  ^ "  -c, --bytes     print the byte count\n"
  ^ "  -h, --help      show this help and exit\n"
  ^ "  -V, --version   show the version and exit\n"

(* Parse [args] without the program name.
 *
 * Hand-rolled rather than cmdliner, because the parser must stay a pure
 * function: no printing, no exit, so each branch is asserted in
 * test/options_test.ml. *)
let parse args =
  let rec loop args figures any_chosen options_ended files =
    match args with
    | [] ->
      let figures = if any_chosen then figures else all_figures in
      { figures; files = List.rev files; status = Ok; message = "" }
    | arg :: rest ->
      if options_ended || arg = "" || arg = "-" then
        loop rest figures any_chosen options_ended (arg :: files)
      else if arg = "--" then
        loop rest figures any_chosen true files
      else if arg = "-h" || arg = "--help" then
        { figures = all_figures; files = List.rev files; status = Help; message = "" }
      else if arg = "-V" || arg = "--version" then
        { figures = all_figures; files = List.rev files; status = Version; message = "" }
      else
        (match arg with
        | "-l" | "--lines" ->
          loop rest { figures with lines = true } true options_ended files
        | "-w" | "--words" ->
          loop rest { figures with words = true } true options_ended files
        | "-c" | "--bytes" ->
          loop rest { figures with bytes = true } true options_ended files
        | _ when String.length arg > 0 && arg.[0] = '-' ->
          {
            figures = all_figures;
            files = List.rev files;
            status = Usage_error;
            message = "unknown option '" ^ arg ^ "'";
          }
        | _ -> loop rest figures any_chosen options_ended (arg :: files))
  in
  loop args no_figures false false []

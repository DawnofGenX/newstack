(* Line, word and byte counting — the only place that decides an answer.
 *
 * Pure: no files, no stdout, no globals. The CLI reads bytes and prints them;
 * this module just counts, so tests drive it directly. *)

type t = {
  lines : int;
  words : int;
  bytes : int;
}

let empty = { lines = 0; words = 0; bytes = 0 }

(* Count [data] with [wc] semantics: [\n] is the only line separator, so a
 * final line without a trailing newline is not a line; words are runs of
 * non-whitespace bytes; bytes are raw bytes, not characters. *)
let of_bytes data =
  let lines = ref 0 in
  let words = ref 0 in
  let in_word = ref false in
  for i = 0 to String.length data - 1 do
    match data.[i] with
    | '\n' ->
      lines := !lines + 1;
      in_word := false
    | ' ' | '\t' | '\r' | '\011' | '\012' ->
      in_word := false
    | _ ->
      if not !in_word then (
        words := !words + 1;
        in_word := true)
  done;
  { lines = !lines; words = !words; bytes = String.length data }

(* Add two totals so several files can be reported as one. *)
let add a b =
  { lines = a.lines + b.lines; words = a.words + b.words; bytes = a.bytes + b.bytes }

let to_string t =
  Printf.sprintf "Counts(lines: %d, words: %d, bytes: %d)" t.lines t.words t.bytes

(* A tiny test harness: no alcotest, no ounit — stdlib only.
 *
 * [check] records a named assertion; [finish] prints the pass/fail tally and
 * exits non-zero if anything failed, so `dune runtest` goes red. *)

let passed = ref 0
let failed = ref 0

let check name cond =
  if cond then
    passed := !passed + 1
  else (
    failed := !failed + 1;
    Printf.eprintf "FAIL %s\n" name)

let check_eq name expected actual =
  check name (expected = actual)

(* Substring search, so a test can assert on captured output without pulling
 * in Str or a regex library. *)
let contains haystack needle =
  let n = String.length needle and h = String.length haystack in
  let rec at i = i + n <= h && (String.sub haystack i n = needle || at (i + 1)) in
  n = 0 || at 0

let check_contains name haystack needle =
  check name (contains haystack needle)

let finish () =
  Printf.printf "%d passed, %d failed\n" !passed !failed;
  if !failed > 0 then exit 1

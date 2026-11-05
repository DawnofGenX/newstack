(* Just enough JSON to tell a string from a number.
 *
 * The stdlib has no parser and pulling yojson in would defeat the point of a
 * zero-dependency stack, so this reads one value and stops. Values keep their
 * raw text so a number can never be mistaken for a string. *)

type value =
  | Str of string
  | Num of string
  | Bool of bool
  | Null
  | List of value list
  | Obj of (string * value) list

exception Malformed of string

type cursor = { text : string; mutable index : int }

let fail cursor message =
  raise (Malformed (Printf.sprintf "%s at byte %d" message cursor.index))

let peek cursor =
  if cursor.index < String.length cursor.text then Some cursor.text.[cursor.index]
  else None

let skip_whitespace cursor =
  let rec loop () =
    match peek cursor with
    | Some (' ' | '\t' | '\n' | '\r') ->
      cursor.index <- cursor.index + 1;
      loop ()
    | _ -> ()
  in
  loop ()

let expect cursor character =
  skip_whitespace cursor;
  match peek cursor with
  | Some found when found = character -> cursor.index <- cursor.index + 1
  | _ -> fail cursor (Printf.sprintf "expected %c" character)

let hex_value character =
  match character with
  | '0' .. '9' -> Char.code character - Char.code '0'
  | 'a' .. 'f' -> Char.code character - Char.code 'a' + 10
  | 'A' .. 'F' -> Char.code character - Char.code 'A' + 10
  | _ -> -1

(* Encodes a code point as UTF-8, so a \uXXXX escape becomes real bytes. *)
let add_utf8 buffer code =
  if code < 0x80 then Buffer.add_char buffer (Char.chr code)
  else if code < 0x800 then (
    Buffer.add_char buffer (Char.chr (0xC0 lor (code lsr 6)));
    Buffer.add_char buffer (Char.chr (0x80 lor (code land 0x3F))))
  else if code < 0x10000 then (
    Buffer.add_char buffer (Char.chr (0xE0 lor (code lsr 12)));
    Buffer.add_char buffer (Char.chr (0x80 lor ((code lsr 6) land 0x3F)));
    Buffer.add_char buffer (Char.chr (0x80 lor (code land 0x3F))))
  else (
    Buffer.add_char buffer (Char.chr (0xF0 lor (code lsr 18)));
    Buffer.add_char buffer (Char.chr (0x80 lor ((code lsr 12) land 0x3F)));
    Buffer.add_char buffer (Char.chr (0x80 lor ((code lsr 6) land 0x3F)));
    Buffer.add_char buffer (Char.chr (0x80 lor (code land 0x3F))))

let read_hex4 cursor =
  if cursor.index + 4 > String.length cursor.text then fail cursor "truncated \\u escape";
  let value = ref 0 in
  for offset = 0 to 3 do
    let digit = hex_value cursor.text.[cursor.index + offset] in
    if digit < 0 then fail cursor "bad \\u escape";
    value := (!value lsl 4) lor digit
  done;
  cursor.index <- cursor.index + 4;
  !value

let handle_escape cursor buffer escape =
  match escape with
  | '"' -> Buffer.add_char buffer '"'
  | '\\' -> Buffer.add_char buffer '\\'
  | '/' -> Buffer.add_char buffer '/'
  | 'b' -> Buffer.add_char buffer '\b'
  | 'f' -> Buffer.add_char buffer '\012'
  | 'n' -> Buffer.add_char buffer '\n'
  | 'r' -> Buffer.add_char buffer '\r'
  | 't' -> Buffer.add_char buffer '\t'
  | 'u' ->
    let code = read_hex4 cursor in
    if code >= 0xD800 && code <= 0xDBFF then
      (* A surrogate pair: the low half follows as another \uXXXX. *)
      if
        cursor.index + 1 < String.length cursor.text
        && cursor.text.[cursor.index] = '\\'
        && cursor.text.[cursor.index + 1] = 'u'
      then (
        cursor.index <- cursor.index + 2;
        let low = read_hex4 cursor in
        add_utf8 buffer (0x10000 + ((code - 0xD800) lsl 10) + (low - 0xDC00)))
      else add_utf8 buffer 0xFFFD
    else add_utf8 buffer code
  | _ -> fail cursor "unknown escape"

let parse_string cursor =
  expect cursor '"';
  let buffer = Buffer.create 16 in
  let rec loop () =
    if cursor.index >= String.length cursor.text then fail cursor "unterminated string";
    let character = cursor.text.[cursor.index] in
    cursor.index <- cursor.index + 1;
    match character with
    | '"' -> Buffer.contents buffer
    | '\\' ->
      if cursor.index >= String.length cursor.text then fail cursor "truncated escape";
      let escape = cursor.text.[cursor.index] in
      cursor.index <- cursor.index + 1;
      handle_escape cursor buffer escape;
      loop ()
    | character when Char.code character < 0x20 -> fail cursor "control character in string"
    | character ->
      Buffer.add_char buffer character;
      loop ()
  in
  loop ()

let parse_number cursor =
  let start = cursor.index in
  let is_digit character = character >= '0' && character <= '9' in
  let consume predicate =
    while
      cursor.index < String.length cursor.text && predicate cursor.text.[cursor.index]
    do
      cursor.index <- cursor.index + 1
    done
  in
  (match peek cursor with
  | Some '-' -> cursor.index <- cursor.index + 1
  | _ -> ());
  consume is_digit;
  (match peek cursor with
  | Some '.' ->
    cursor.index <- cursor.index + 1;
    consume is_digit
  | _ -> ());
  (match peek cursor with
  | Some ('e' | 'E') ->
    cursor.index <- cursor.index + 1;
    (match peek cursor with
    | Some ('+' | '-') -> cursor.index <- cursor.index + 1
    | _ -> ());
    consume is_digit
  | _ -> ());
  if cursor.index = start then fail cursor "expected a number";
  String.sub cursor.text start (cursor.index - start)

let literal cursor word value =
  let length = String.length word in
  if cursor.index + length > String.length cursor.text then fail cursor ("expected " ^ word);
  if String.sub cursor.text cursor.index length = word then (
    cursor.index <- cursor.index + length;
    value)
  else fail cursor ("expected " ^ word)

let rec parse_value cursor =
  skip_whitespace cursor;
  match peek cursor with
  | None -> fail cursor "unexpected end of input"
  | Some '"' -> Str (parse_string cursor)
  | Some '{' -> parse_object cursor
  | Some '[' -> parse_array cursor
  | Some 't' -> literal cursor "true" (Bool true)
  | Some 'f' -> literal cursor "false" (Bool false)
  | Some 'n' -> literal cursor "null" Null
  | Some _ -> Num (parse_number cursor)

and parse_object cursor =
  expect cursor '{';
  let rec members accumulated =
    skip_whitespace cursor;
    match peek cursor with
    | Some '}' ->
      cursor.index <- cursor.index + 1;
      Obj (List.rev accumulated)
    | _ ->
      let name = parse_string cursor in
      expect cursor ':';
      let value = parse_value cursor in
      skip_whitespace cursor;
      (match peek cursor with
      | Some ',' ->
        cursor.index <- cursor.index + 1;
        members ((name, value) :: accumulated)
      | Some '}' ->
        cursor.index <- cursor.index + 1;
        Obj (List.rev ((name, value) :: accumulated))
      | _ -> fail cursor "expected ',' or '}'")
  in
  members []

and parse_array cursor =
  expect cursor '[';
  let rec elements accumulated =
    skip_whitespace cursor;
    match peek cursor with
    | Some ']' ->
      cursor.index <- cursor.index + 1;
      List (List.rev accumulated)
    | _ ->
      let value = parse_value cursor in
      skip_whitespace cursor;
      (match peek cursor with
      | Some ',' ->
        cursor.index <- cursor.index + 1;
        elements (value :: accumulated)
      | Some ']' ->
        cursor.index <- cursor.index + 1;
        List (List.rev (value :: accumulated))
      | _ -> fail cursor "expected ',' or ']'")
  in
  elements []

(* The value must be the whole document: trailing bytes are a syntax error,
 * unlike some parsers that stop at the end of the first value. *)
let decode text =
  let cursor = { text; index = 0 } in
  let value = parse_value cursor in
  skip_whitespace cursor;
  if cursor.index <> String.length text then fail cursor "trailing data";
  value

type text_kind =
  | Invalid
  | Missing
  | Text of string

(* Reads the "text" field out of a JSON body, keeping "42" apart from 42. *)
let read_text body =
  match decode body with
  | exception Malformed _ -> Invalid
  | Obj members -> (
    match List.assoc_opt "text" members with
    | Some (Str text) -> Text text
    | Some _ -> Missing
    | None -> Missing)
  | _ -> Invalid

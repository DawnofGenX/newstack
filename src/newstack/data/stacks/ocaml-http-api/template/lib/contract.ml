(* The route table, pure: method/path/query/body in, status and body out.
 *
 * Nothing here touches a socket, so every status code is a plain function call
 * in the tests and the server is a thin adapter. *)

type reply = { status : int; body : string }

let escape_json text =
  let buffer = Buffer.create (String.length text + 2) in
  String.iter
    (fun character ->
      match character with
      | '"' -> Buffer.add_string buffer "\\\""
      | '\\' -> Buffer.add_string buffer "\\\\"
      | '\n' -> Buffer.add_string buffer "\\n"
      | '\r' -> Buffer.add_string buffer "\\r"
      | '\t' -> Buffer.add_string buffer "\\t"
      | character when Char.code character < 0x20 ->
        Buffer.add_string buffer (Printf.sprintf "\\u%04x" (Char.code character))
      | character -> Buffer.add_char buffer character)
    text;
  Buffer.contents buffer

let quoted text = "\"" ^ escape_json text ^ "\""

let counts_json text counts =
  Printf.sprintf "{\"text\":%s,\"lines\":%d,\"words\":%d,\"bytes\":%d}" (quoted text)
    counts.Counts.lines counts.Counts.words counts.Counts.bytes

let error status code detail =
  {
    status;
    body =
      (match detail with
      | None -> Printf.sprintf "{\"error\":%s}" (quoted code)
      | Some detail ->
        Printf.sprintf "{\"error\":%s,\"detail\":%s}" (quoted code) (quoted detail));
  }

let percent_decode text =
  let buffer = Buffer.create (String.length text) in
  let hex character =
    match character with
    | '0' .. '9' -> Char.code character - Char.code '0'
    | 'a' .. 'f' -> Char.code character - Char.code 'a' + 10
    | 'A' .. 'F' -> Char.code character - Char.code 'A' + 10
    | _ -> -1
  in
  let rec loop index =
    if index >= String.length text then ()
    else
      match text.[index] with
      | '%' when index + 2 < String.length text ->
        let high = hex text.[index + 1] and low = hex text.[index + 2] in
        if high >= 0 && low >= 0 then (
          Buffer.add_char buffer (Char.chr ((high lsl 4) lor low));
          loop (index + 3))
        else (
          Buffer.add_char buffer '%';
          loop (index + 1))
      | '+' ->
        Buffer.add_char buffer ' ';
        loop (index + 1)
      | character ->
        Buffer.add_char buffer character;
        loop (index + 1)
  in
  loop 0;
  Buffer.contents buffer

(* Reads one "&"-separated pair, decoding "+" and "%XX". *)
let query_param query name =
  let length = String.length query in
  let rec scan index =
    if index > length then None
    else
      let close =
        match String.index_from_opt query index '&' with
        | Some position -> position
        | None -> length
      in
      let pair = String.sub query index (close - index) in
      let key, value =
        match String.index_opt pair '=' with
        | Some position ->
          ( String.sub pair 0 position,
            String.sub pair (position + 1) (String.length pair - position - 1) )
        | None -> (pair, "")
      in
      if key = name then Some (percent_decode value)
      else if close >= length then None
      else scan (close + 1)
  in
  scan 0

let method_not_allowed = error 405 "method_not_allowed" None

let not_found method_ path =
  error 404 "not_found" (Some (Printf.sprintf "no route for %s %s" method_ path))

let route method_ path query body =
  match (method_, path) with
  | "GET", "/health" -> { status = 200; body = "{\"status\":\"ok\"}" }
  | "GET", "/stats" -> (
    match query_param query "text" with
    | Some text -> { status = 200; body = counts_json text (Counts.of_bytes text) }
    | None -> error 422 "missing_text" None)
  | "POST", "/stats" -> (
    match Json.read_text body with
    | Json.Text text -> { status = 200; body = counts_json text (Counts.of_bytes text) }
    | Json.Missing -> error 422 "missing_text" None
    | Json.Invalid -> error 422 "invalid_json" None)
  | _, ("/health" | "/stats") -> method_not_allowed
  | _ -> not_found method_ path

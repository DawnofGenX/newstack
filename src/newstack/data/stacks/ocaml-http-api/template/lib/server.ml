(* A blocking HTTP/1.1 loop on the Unix module: one request per connection. *)

let max_header = 8192
let max_body = 65536

type request = { method_ : string; path : string; query : string; body : string }

let status_text = function
  | 200 -> "OK"
  | 404 -> "Not Found"
  | 405 -> "Method Not Allowed"
  | 413 -> "Payload Too Large"
  | 422 -> "Unprocessable Entity"
  | 500 -> "Internal Server Error"
  | _ -> "Unknown"

(* Reads until the blank line that ends the head, or the cap. *)
let read_head file_descriptor =
  let buffer = Buffer.create 256 in
  let chunk = Bytes.create 1 in
  let complete head =
    let length = String.length head in
    length >= 4 && String.sub head (length - 4) 4 = "\r\n\r\n"
  in
  let rec loop head =
    if String.length head >= max_header then head
    else
      match Unix.read file_descriptor chunk 0 1 with
      | 0 -> head
      | _ ->
        let head = head ^ Bytes.sub_string chunk 0 1 in
        if complete head then head else loop head
  in
  ignore buffer;
  loop ""

let split_on character text =
  let rec loop start accumulated =
    match String.index_from_opt text start character with
    | Some position ->
      loop (position + 1) (String.sub text start (position - start) :: accumulated)
    | None -> List.rev (String.sub text start (String.length text - start) :: accumulated)
  in
  loop 0 []

let lowercase text = String.lowercase_ascii text

let trim text =
  let is_space = function ' ' | '\t' | '\r' | '\n' -> true | _ -> false in
  let length = String.length text in
  let first = ref 0 in
  while !first < length && is_space text.[!first] do
    incr first
  done;
  let last = ref (length - 1) in
  while !last >= !first && is_space text.[!last] do
    decr last
  done;
  String.sub text !first (!last - !first + 1)

let parse_head head =
  match split_on '\n' head with
  | [] -> None
  | first :: rest -> (
    let first = trim first in
    match split_on ' ' first with
    | method_ :: target :: _ -> (
      let path, query =
        match String.index_opt target '?' with
        | Some position ->
          ( String.sub target 0 position,
            String.sub target (position + 1) (String.length target - position - 1) )
        | None -> (target, "")
      in
      let content_length =
        List.fold_left
          (fun found line ->
            let line = trim line in
            match String.index_opt line ':' with
            | None -> found
            | Some colon ->
              let name = lowercase (String.sub line 0 colon) in
              if name = "content-length" then
                match
                  int_of_string_opt (trim (String.sub line (colon + 1) (String.length line - colon - 1)))
                with
                | Some value -> value
                | None -> found
              else found)
          0 rest
      in
      Some ({ method_; path; query; body = "" }, content_length))
    | _ -> None)

let read_body file_descriptor head length =
  let blank =
    let rec find index =
      if index + 4 > String.length head then String.length head
      else if String.sub head index 4 = "\r\n\r\n" then index
      else find (index + 1)
    in
    find 0
  in
  let buffer = Buffer.create (max length 32) in
  Buffer.add_string buffer
    (String.sub head (blank + 4) (max 0 (String.length head - blank - 4)));
  let chunk = Bytes.create 4096 in
  let rec loop () =
    if Buffer.length buffer < length then
      match Unix.read file_descriptor chunk 0 (min 4096 (length - Buffer.length buffer)) with
      | 0 -> ()
      | count ->
        Buffer.add_subbytes buffer chunk 0 count;
        loop ()
  in
  loop ();
  let body = Buffer.contents buffer in
  if String.length body > length then String.sub body 0 length else body

let respond file_descriptor reply =
  let head =
    Printf.sprintf
      "HTTP/1.1 %d %s\r\ncontent-type: application/json\r\ncontent-length: %d\r\nconnection: close\r\n\r\n"
      reply.Contract.status (status_text reply.Contract.status)
      (String.length reply.Contract.body)
  in
  let payload = head ^ reply.Contract.body in
  let rec write offset =
    if offset < String.length payload then
      let sent = Unix.write_substring file_descriptor payload offset (String.length payload - offset) in
      if sent > 0 then write (offset + sent)
  in
  write 0

let handle file_descriptor =
  let head = read_head file_descriptor in
  match parse_head head with
  | None -> respond file_descriptor { Contract.status = 422; body = "{\"error\":\"bad_request\"}" }
  | Some (request, length) ->
    if length > max_body then
      respond file_descriptor { Contract.status = 413; body = "{\"error\":\"body_too_large\"}" }
    else
      let body = read_body file_descriptor head length in
      respond file_descriptor
        (Contract.route request.method_ request.path request.query body)

let serve host port =
  ignore (Sys.signal Sys.sigpipe Sys.Signal_ignore);
  let socket = Unix.socket Unix.PF_INET Unix.SOCK_STREAM 0 in
  Unix.setsockopt socket Unix.SO_REUSEADDR true;
  Unix.bind socket (Unix.ADDR_INET (Unix.inet_addr_of_string host, port));
  Unix.listen socket 16;
  Printf.printf "listening on http://%s:%d\n%!" host port;
  while true do
    let client, _ = Unix.accept socket in
    (try handle client with _ -> ());
    (try Unix.close client with _ -> ())
  done

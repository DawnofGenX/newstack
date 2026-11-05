module Textstat.Json

// A JSON reader for the one document this service accepts: an object with a
// "text" member that is a string. Everything else still has to be valid JSON, so
// this walks values properly instead of pattern matching, and every string is
// handled as bytes — a request body is not text until it has been decoded.

open System

/// What the body said. "invalid" is a broken document; "missing" is a valid one
/// without a text string, which includes a text member of the wrong type.
type Body =
    | Text of byte[]
    | MissingText
    | Invalid

exception Malformed

let private skipWhitespace (raw: byte[]) (pos: int ref) =
    while !pos < raw.Length && (raw.[!pos] = 32uy || raw.[!pos] = 9uy || raw.[!pos] = 10uy || raw.[!pos] = 13uy) do
        pos := !pos + 1

let private encodeCodePoint (code: int) : byte[] =
    if code < 0 || code > 0x10FFFF then raise Malformed
    Text.Encoding.UTF8.GetBytes(Char.ConvertFromUtf32(code))

let private hexValue (raw: byte[]) (start: int) : int =
    let mutable value = 0
    for i in start .. start + 3 do
        if i >= raw.Length then raise Malformed
        let c = int raw.[i]
        let digit =
            if c >= int '0' && c <= int '9' then c - int '0'
            elif c >= int 'a' && c <= int 'f' then c - int 'a' + 10
            elif c >= int 'A' && c <= int 'F' then c - int 'A' + 10
            else raise Malformed
        value <- value * 16 + digit
    value

/// Scans one string literal into bytes, from the opening quote to just past the
/// closing one.
let private scanString (raw: byte[]) (pos: int ref) : byte[] =
    let out = ResizeArray<byte>()
    let mutable i = !pos + 1
    let mutable done_ = false
    while not done_ do
        if i >= raw.Length then raise Malformed
        let b = int raw.[i]
        if b = int '"' then
            pos := i + 1
            done_ <- true
        elif b <> int '\\' then
            out.Add raw.[i]
            i <- i + 1
        else
            if i + 1 >= raw.Length then raise Malformed
            let esc = int raw.[i + 1]
            let single ch =
                out.Add(byte ch)
                i <- i + 2
            match esc with
            | _ when esc = int '"' -> single '"'
            | _ when esc = int '\\' -> single '\\'
            | _ when esc = int '/' -> single '/'
            | _ when esc = int 'b' -> single (char 8)
            | _ when esc = int 'f' -> single (char 12)
            | _ when esc = int 'n' -> single (char 10)
            | _ when esc = int 'r' -> single (char 13)
            | _ when esc = int 't' -> single (char 9)
            | _ when esc = int 'u' ->
                let mutable code = hexValue raw (i + 2)
                i <- i + 6
                if code >= 0xD800 && code <= 0xDBFF then
                    if i + 1 >= raw.Length || int raw.[i] <> int '\\' || int raw.[i + 1] <> int 'u' then
                        raise Malformed
                    let low = hexValue raw (i + 2)
                    if low < 0xDC00 || low > 0xDFFF then raise Malformed
                    code <- 0x10000 + (code - 0xD800) * 1024 + (low - 0xDC00)
                    i <- i + 6
                elif code >= 0xDC00 && code <= 0xDFFF then
                    raise Malformed
                for value in encodeCodePoint code do
                    out.Add value
            | _ -> raise Malformed
    out.ToArray()

let rec private skipValue (raw: byte[]) (pos: int ref) (depth: int) : unit =
    if depth > 32 then raise Malformed
    skipWhitespace raw pos
    if !pos >= raw.Length then raise Malformed
    let b = int raw.[!pos]
    if b = int '"' then
        scanString raw pos |> ignore
    elif b = int '{' || b = int '[' then
        let closer = if b = int '{' then int '}' else int ']'
        let isObject = b = int '{'
        pos := !pos + 1
        skipWhitespace raw pos
        if !pos < raw.Length && int raw.[!pos] = closer then
            pos := !pos + 1
        else
            let mutable stop = false
            while not stop do
                if isObject then
                    skipWhitespace raw pos
                    if !pos >= raw.Length || int raw.[!pos] <> int '"' then raise Malformed
                    scanString raw pos |> ignore
                    skipWhitespace raw pos
                    if !pos >= raw.Length || int raw.[!pos] <> int ':' then raise Malformed
                    pos := !pos + 1
                skipValue raw pos (depth + 1)
                skipWhitespace raw pos
                if !pos >= raw.Length then raise Malformed
                let c = int raw.[!pos]
                if c = closer then
                    pos := !pos + 1
                    stop <- true
                elif c = int ',' then
                    pos := !pos + 1
                else
                    raise Malformed
    else
        let start = !pos
        let mutable i = !pos
        let mutable scanning = true
        while scanning do
            if i >= raw.Length then
                scanning <- false
            else
                let c = int raw.[i]
                if c = int ',' || c = int '}' || c = int ']' || c = 32 || c = 9 || c = 10 || c = 13 then
                    scanning <- false
                else
                    i <- i + 1
        if i = start then raise Malformed
        pos := i

/// Reads a request body. Only the last "text" member counts, and a text member
/// that is not a string leaves the document without text rather than broken.
let read (raw: byte[]) : Body =
    let pos = ref 0
    try
        skipWhitespace raw pos
        if !pos >= raw.Length || int raw.[!pos] <> int '{' then
            Invalid
        else
            pos := !pos + 1
            let mutable found = None
            let mutable stop = false
            skipWhitespace raw pos
            if !pos < raw.Length && int raw.[!pos] = int '}' then
                pos := !pos + 1
                stop <- true
            while not stop do
                skipWhitespace raw pos
                if !pos >= raw.Length || int raw.[!pos] <> int '"' then raise Malformed
                let key = scanString raw pos
                skipWhitespace raw pos
                if !pos >= raw.Length || int raw.[!pos] <> int ':' then raise Malformed
                pos := !pos + 1
                skipWhitespace raw pos
                if !pos < raw.Length && int raw.[!pos] = int '"' && Array.toList key = (Text.Encoding.ASCII.GetBytes "text" |> Array.toList) then
                    found <- Some(scanString raw pos)
                else
                    if Array.toList key = (Text.Encoding.ASCII.GetBytes "text" |> Array.toList) then
                        found <- None
                    skipValue raw pos 1
                skipWhitespace raw pos
                if !pos >= raw.Length then raise Malformed
                let c = int raw.[!pos]
                if c = int '}' then
                    pos := !pos + 1
                    stop <- true
                elif c = int ',' then
                    pos := !pos + 1
                else
                    raise Malformed
            skipWhitespace raw pos
            if !pos < raw.Length then raise Malformed
            match found with
            | Some bytes -> Text bytes
            | None -> MissingText
    with
    | Malformed -> Invalid
    | :? ArgumentException -> Invalid

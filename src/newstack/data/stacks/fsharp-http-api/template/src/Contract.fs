module Textstat.Contract

// The route table as one pure function: method, target and body in, a status and
// a JSON document out. Nothing here opens a socket, so the whole contract is
// testable in-process.

open System
open Textstat.Counts
open Textstat.Json

type Reply = { Status: int; Body: byte[] }

let private ascii (text: string) = Text.Encoding.ASCII.GetBytes text

let private escape (raw: byte[]) : byte[] =
    let out = ResizeArray<byte>()
    for b in raw do
        match int b with
        | 0x22 -> out.AddRange(ascii "\\\"")
        | 0x5C -> out.AddRange(ascii "\\\\")
        | 0x0A -> out.AddRange(ascii "\\n")
        | 0x0D -> out.AddRange(ascii "\\r")
        | 0x09 -> out.AddRange(ascii "\\t")
        | 0x08 -> out.AddRange(ascii "\\b")
        | 0x0C -> out.AddRange(ascii "\\f")
        | c when c < 0x20 -> out.AddRange(ascii (sprintf "\\u%04x" c))
        | _ -> out.Add b
    out.ToArray()

let private concat (parts: byte[] list) : byte[] =
    parts |> List.collect Array.toList |> Array.ofList

let private percentDecode (raw: string) : byte[] =
    let source = Text.Encoding.UTF8.GetBytes raw
    let out = ResizeArray<byte>()
    let mutable i = 0
    let hex (b: byte) =
        let c = int b
        if c >= int '0' && c <= int '9' then c - int '0'
        elif c >= int 'a' && c <= int 'f' then c - int 'a' + 10
        elif c >= int 'A' && c <= int 'F' then c - int 'A' + 10
        else -1
    while i < source.Length do
        let b = int source.[i]
        if b = int '+' then
            out.Add 32uy
            i <- i + 1
        elif b = int '%' && i + 2 < source.Length && hex source.[i + 1] >= 0 && hex source.[i + 2] >= 0 then
            out.Add(byte (hex source.[i + 1] * 16 + hex source.[i + 2]))
            i <- i + 3
        else
            out.Add source.[i]
            i <- i + 1
    out.ToArray()

/// Query parameters, first occurrence wins, and a leading '?' in the target is
/// just part of the URL.
let queryText (target: string) : byte[] option =
    match target.IndexOf '?' with
    | -1 -> None
    | mark ->
        let query = target.Substring(mark + 1)
        let mutable found = None
        for piece in query.Split '&' do
            if piece <> "" && found.IsNone then
                let eq = piece.IndexOf '='
                let key, value =
                    if eq < 0 then piece, "" else piece.Substring(0, eq), piece.Substring(eq + 1)
                if percentDecode key = ascii "text" then
                    found <- Some(percentDecode value)
        found

let private statsBody (text: byte[]) : byte[] =
    let counts = count text
    concat
        [ ascii "{\"text\":\""
          escape text
          ascii (sprintf "\",\"lines\":%d,\"words\":%d,\"bytes\":%d}" counts.Lines counts.Words counts.Bytes) ]

let reply status body = { Status = status; Body = body }

let private errorDoc (code: string) = ascii (sprintf "{\"error\":\"%s\"}" code)

let route (method: string) (target: string) (body: byte[]) : Reply =
    let path =
        match target.IndexOf '?' with
        | -1 -> target
        | mark -> target.Substring(0, mark)

    match path with
    | "/health" ->
        if method <> "GET" then
            reply 405 (errorDoc "method_not_allowed")
        else
            reply 200 (ascii "{\"status\":\"ok\"}")
    | "/stats" ->
        if method = "GET" then
            match queryText target with
            | Some text -> reply 200 (statsBody text)
            | None -> reply 422 (errorDoc "missing_text")
        elif method = "POST" then
            match Json.read body with
            | Text text -> reply 200 (statsBody text)
            | MissingText -> reply 422 (errorDoc "missing_text")
            | Invalid -> reply 422 (errorDoc "invalid_json")
        else
            reply 405 (errorDoc "method_not_allowed")
    | _ ->
        reply
            404
            (concat
                [ ascii "{\"error\":\"not_found\",\"detail\":\"no route for "
                  escape (Text.Encoding.UTF8.GetBytes method)
                  ascii " "
                  escape (Text.Encoding.UTF8.GetBytes target)
                  ascii "\"}" ])

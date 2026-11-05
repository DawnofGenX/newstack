module Textstat.Server

// One connection at a time on a plain TcpListener: read until CRLFCRLF, read
// exactly Content-Length bytes, answer, close. No framework, so nothing between
// the bytes on the wire and the counting core.

open System
open System.Net
open System.Net.Sockets
open Textstat.Contract

let private reason (status: int) =
    match status with
    | 200 -> "OK"
    | 404 -> "Not Found"
    | 405 -> "Method Not Allowed"
    | _ -> "Unprocessable Entity"

let private readHead (stream: NetworkStream) : byte[] option =
    // The head is small and the terminator is four bytes, so reading a byte at a
    // time keeps the body in the socket instead of in an over-read buffer.
    let head = ResizeArray<byte>()
    let mutable done_ = false
    let mutable over = false
    while not done_ && not over do
        let value = stream.ReadByte()
        if value < 0 then
            over <- true
        else
            head.Add(byte value)
            let n = head.Count
            if n >= 4 && head.[n - 4] = 13uy && head.[n - 3] = 10uy && head.[n - 2] = 13uy && head.[n - 1] = 10uy then
                done_ <- true
            elif n > 16384 then
                over <- true
    if done_ then Some(head.ToArray()) else None

let private contentLength (lines: string[]) =
    lines
    |> Array.skip 1
    |> Array.tryPick (fun line ->
        match line.IndexOf ':' with
        | -1 -> None
        | i when line.Substring(0, i).Trim().ToLowerInvariant() = "content-length" ->
            match Int32.TryParse(line.Substring(i + 1).Trim()) with
            | true, value -> Some value
            | _ -> None
        | _ -> None)
    |> Option.defaultValue 0

let private respond (stream: NetworkStream) (reply: Reply) =
    let head =
        Text.Encoding.ASCII.GetBytes(
            sprintf
                "HTTP/1.1 %d %s\r\ncontent-type: application/json\r\ncontent-length: %d\r\nconnection: close\r\n\r\n"
                reply.Status
                (reason reply.Status)
                reply.Body.Length
        )
    stream.Write(head, 0, head.Length)
    stream.Write(reply.Body, 0, reply.Body.Length)
    stream.Flush()

let private handle (stream: NetworkStream) =
    match readHead stream with
    | None -> ()
    | Some rawHead ->
        let head = Text.Encoding.ASCII.GetString rawHead
        let lines = head.Split("\r\n")
        if lines.Length > 0 then
            let parts = lines.[0].Split(' ')
            if parts.Length >= 2 then
                let length = min (contentLength lines) 65536
                let body = Array.zeroCreate length
                let mutable read = 0
                while read < length do
                    let n = stream.Read(body, read, length - read)
                    if n <= 0 then read <- length else read <- read + n
                respond stream (route parts.[0] parts.[1] body)

let serve (host: string) (port: int) =
    let listener = new TcpListener(IPAddress.Parse host, port)
    listener.Server.SetSocketOption(SocketOptionLevel.Socket, SocketOptionName.ReuseAddress, true)
    listener.Start()
    while true do
        let client = listener.AcceptTcpClient()
        try
            use stream = client.GetStream()
            try
                handle stream
            with
            | :? IO.IOException -> ()
        finally
            client.Close()

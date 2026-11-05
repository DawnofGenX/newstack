module Textstat.Program

open System

[<EntryPoint>]
let main argv =
    if argv |> Array.contains "--selftest" then
        Textstat.Tests.run ()
    else
        let host =
            match Environment.GetEnvironmentVariable "HOST" with
            | null | "" -> "127.0.0.1"
            | value -> value
        let port =
            match Environment.GetEnvironmentVariable "PORT" with
            | null | "" -> 8080
            | value ->
                match Int32.TryParse value with
                | true, number when number > 0 && number < 65536 -> number
                | _ ->
                    Console.Error.WriteLine(sprintf "PORT is not a port: %s" value)
                    exit 2
        Textstat.Server.serve host port
        0

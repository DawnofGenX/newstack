namespace {{ package_name }}

open System

/// <summary>Which figures to print; <c>All</c> prints lines, words and bytes.</summary>
type Mode =
    | All
    | Lines
    | Words
    | Bytes

/// <summary>How argument parsing ended.</summary>
type Status =
    | Ok
    | Help
    | Version
    | Error

/// <summary>Parsed command line: the chosen mode, the files, and how parsing ended.</summary>
type Options =
    { Mode: Mode
      Files: string list
      Status: Status
      Error: string }

/// <summary>Hand-rolled argv parsing: no dependency, and every branch is unit tested.</summary>
[<RequireQualifiedAccess>]
module Options =

    [<Literal>]
    let Version = "0.1.0"

    let private modeFor (argument: string) : Mode option =
        match argument with
        | "-l" | "--lines" -> Some Mode.Lines
        | "-w" | "--words" -> Some Mode.Words
        | "-c" | "--bytes" -> Some Mode.Bytes
        | _ -> None

    /// <summary>Parses argv. Never prints and never exits: the caller owns both.</summary>
    let parse (args: string[]) : Options =
        let rec loop (chosen: Mode option) (onlyFiles: bool) (files: string list) (remaining: string list) : Options =
            match remaining with
            | [] ->
                { Mode = defaultArg chosen Mode.All
                  Files = List.rev files
                  Status = Status.Ok
                  Error = "" }
            | argument :: rest ->
                if onlyFiles || argument = "" || argument = "-" then
                    loop chosen onlyFiles (argument :: files) rest
                elif argument = "--" then
                    loop chosen true files rest
                elif argument = "-h" || argument = "--help" then
                    { Mode = defaultArg chosen Mode.All
                      Files = List.rev files
                      Status = Status.Help
                      Error = "" }
                elif argument = "-V" || argument = "--version" then
                    { Mode = defaultArg chosen Mode.All
                      Files = List.rev files
                      Status = Status.Version
                      Error = "" }
                else
                    match modeFor argument with
                    | Some requested ->
                        match chosen with
                        | Some earlier when earlier <> requested ->
                            { Mode = earlier
                              Files = List.rev files
                              Status = Status.Error
                              Error = $"choose one of -l, -w, -c: '{argument}' conflicts with an earlier mode" }
                        | _ -> loop (Some requested) onlyFiles files rest
                    | None ->
                        if argument.StartsWith "-" then
                            { Mode = defaultArg chosen Mode.All
                              Files = List.rev files
                              Status = Status.Error
                              Error = $"unknown option '{argument}'" }
                        else
                            loop chosen onlyFiles (argument :: files) rest

        loop None false [] (List.ofArray args)

    /// <summary>Help text; the program name is passed in so it matches the binary.</summary>
    let usage (program: string) : string =
        String.concat
            "\n"
            [ $"usage: {program} [-l | -w | -c] [--] [FILE ...]"
              ""
              "Count lines, words and bytes in each FILE, or in standard input"
              "when no FILE is given. With more than one FILE a total is printed."
              ""
              "  -l, --lines     print the line count only"
              "  -w, --words     print the word count only"
              "  -c, --bytes     print the byte count only"
              "  -h, --help      show this help and exit"
              "  -V, --version   show the version and exit" ]
        + "\n"

module Program

open System
open System.Globalization
open System.IO

open {{ package_name }}

/// <summary>Right-aligns one figure the way <c>wc</c> pads its columns.</summary>
let private format (value: int64) : string =
    value.ToString CultureInfo.InvariantCulture
    |> fun digits -> digits.PadLeft 8

/// <summary>Prints the figures selected by <paramref name="mode"/>, then the label.</summary>
let private print (output: TextWriter) (counts: Counts) (mode: Mode) (label: string) : unit =
    let figures =
        [ if mode = Mode.All || mode = Mode.Lines then
              yield format counts.Lines
          if mode = Mode.All || mode = Mode.Words then
              yield format counts.Words
          if mode = Mode.All || mode = Mode.Bytes then
              yield format counts.Bytes ]

    let line = String.Join("", figures)
    if String.IsNullOrEmpty label then
        output.WriteLine line
    else
        output.WriteLine(line + " " + label)

/// <summary>Reads standard input once; returns None when it cannot be read.</summary>
let private readStandardInput () : Counts option =
    try
        Some(Counts.ofString (Console.In.ReadToEnd()))
    with :? IOException ->
        None

let private countFiles (options: Options) : int =
    let mutable total = Counts.zero
    let mutable failed = false

    for path in options.Files do
        let counted =
            if path = "-" then
                match readStandardInput () with
                | Some counts -> Some counts
                | None ->
                    Console.Error.WriteLine "error: cannot read standard input"
                    failed <- true
                    None
            else
                try
                    Some(Counts.ofBytes (File.ReadAllBytes path))
                with
                | :? IOException
                | :? UnauthorizedAccessException ->
                    Console.Error.WriteLine $"error: cannot open '{path}'"
                    failed <- true
                    None

        match counted with
        | Some counts ->
            print Console.Out counts options.Mode (if path = "-" then "" else path)
            total <- Counts.plus total counts
        | None -> ()

    if List.length options.Files > 1 then
        print Console.Out total options.Mode "total"

    if failed then 1 else 0

/// <summary>
/// The thin entry point: the only place that prints and sets an exit code.
/// Exit codes: 0 success, 1 unreadable input, 2 bad usage.
/// </summary>
[<EntryPoint>]
let main argv =
    let program = "{{ npm_name }}"
    let options = Options.parse argv

    let code =
        match options.Status with
        | Status.Help ->
            Console.Out.Write(Options.usage program)
            0
        | Status.Version ->
            Console.Out.WriteLine Options.Version
            0
        | Status.Error ->
            Console.Error.WriteLine("error: " + options.Error)
            Console.Error.WriteLine()
            Console.Error.Write(Options.usage program)
            2
        | Status.Ok ->
            if List.isEmpty options.Files then
                match readStandardInput () with
                | Some counts ->
                    print Console.Out counts options.Mode ""
                    0
                | None ->
                    Console.Error.WriteLine "error: cannot read standard input"
                    1
            else
                countFiles options

    exit code

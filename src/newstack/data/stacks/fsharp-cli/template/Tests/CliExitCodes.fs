module {{ package_name }}.Tests.CliExitCodes

open System
open System.Diagnostics
open System.IO

open Xunit

/// <summary>
/// Exit codes are a contract, so these tests launch the real built binary as a
/// process instead of calling a function in process. `dotnet test` builds the exe
/// first because the test project references App.fsproj.
/// </summary>

let private binaryName = "{{ npm_name }}"

// Both paths are functions rather than values: F# module-level values in this
// assembly are default-initialised when the runner invokes a test, so reading
// them here would see "" instead of the computed path.
let private projectRoot () =
    let rec climb (directory: DirectoryInfo) =
        if isNull directory then
            failwith "could not find App.fsproj above the test output directory"
        elif File.Exists(Path.Combine(directory.FullName, "App.fsproj")) then
            directory.FullName
        else
            climb directory.Parent

    climb (DirectoryInfo AppContext.BaseDirectory)

let private executable () =
    let candidates =
        [ for configuration in [ "Debug"; "Release" ] do
              Path.Combine(projectRoot (), "bin", configuration, "net8.0", binaryName) ]

    match candidates |> List.tryFind File.Exists with
    | Some path -> path
    | None ->
        let looked = String.Join(", ", candidates)
        failwith $"the built binary is missing; run `dotnet build` first (looked for {looked})"

type private Outcome =
    { ExitCode: int
      Stdout: string
      Stderr: string }

let private launch (arguments: string list) : Outcome =
    let startInfo = ProcessStartInfo(executable ())
    startInfo.UseShellExecute <- false
    startInfo.RedirectStandardOutput <- true
    startInfo.RedirectStandardError <- true

    for argument in arguments do
        startInfo.ArgumentList.Add argument

    use process = Process.Start startInfo
    let stdout = process.StandardOutput.ReadToEndAsync()
    let stderr = process.StandardError.ReadToEndAsync()
    process.WaitForExit()

    { ExitCode = process.ExitCode
      Stdout = stdout.Result
      Stderr = stderr.Result }

let private withTempFile (contents: string) (assertions: string -> unit) =
    let path = Path.Combine(Path.GetTempPath(), Path.GetRandomFileName())
    File.WriteAllText(path, contents)

    try
        assertions path
    finally
        File.Delete path

[<Fact>]
let ``help prints the usage line for this binary and exits zero`` () =
    let outcome = launch [ "--help" ]

    Assert.Equal(0, outcome.ExitCode)
    Assert.StartsWith("usage: " + binaryName, outcome.Stdout)
    Assert.Equal("", outcome.Stderr)

[<Fact>]
let ``version prints the version and exits zero`` () =
    let outcome = launch [ "--version" ]

    Assert.Equal(0, outcome.ExitCode)
    Assert.Equal("0.1.0", outcome.Stdout.Trim())

[<Fact>]
let ``a bad flag exits two and explains itself on stderr`` () =
    let outcome = launch [ "--bogus" ]

    Assert.Equal(2, outcome.ExitCode)
    Assert.Contains("error: unknown option '--bogus'", outcome.Stderr)
    Assert.Contains("usage: ", outcome.Stderr)
    Assert.Equal("", outcome.Stdout)

[<Fact>]
let ``a missing file exits one`` () =
    let outcome = launch [ "does-not-exist.txt" ]

    Assert.Equal(1, outcome.ExitCode)
    Assert.Contains("error: cannot open 'does-not-exist.txt'", outcome.Stderr)

[<Fact>]
let ``a terminated final line is counted`` () =
    withTempFile "one two\nthree\n" (fun path ->
        let outcome = launch [ path ]

        Assert.Equal(0, outcome.ExitCode)
        Assert.Equal<string[]>(
            [| "2"; "3"; "14"; path |],
            outcome.Stdout.Trim().Split(' ', StringSplitOptions.RemoveEmptyEntries)
        ))

[<Fact>]
let ``an unterminated final line is not counted, and its bytes are`` () =
    withTempFile "one two\nthree" (fun path ->
        let outcome = launch [ path ]

        Assert.Equal(0, outcome.ExitCode)
        Assert.Equal<string[]>(
            [| "1"; "3"; "13"; path |],
            outcome.Stdout.Trim().Split(' ', StringSplitOptions.RemoveEmptyEntries)
        ))

[<Fact>]
let ``one mode flag prints one figure`` () =
    withTempFile "alpha beta gamma\n" (fun path ->
        let outcome = launch [ "-w"; path ]

        Assert.Equal(0, outcome.ExitCode)
        Assert.Equal<string[]>(
            [| "3"; path |],
            outcome.Stdout.Trim().Split(' ', StringSplitOptions.RemoveEmptyEntries)
        ))

[<Fact>]
let ``several files get a total line`` () =
    withTempFile "a b\n" (fun first ->
        withTempFile "c\n" (fun second ->
            let outcome = launch [ "-l"; first; second ]

            Assert.Equal(0, outcome.ExitCode)
            let rows = outcome.Stdout.Trim().Split('\n')
            Assert.Equal(3, rows.Length)
            Assert.EndsWith("total", rows[2])))

module {{ package_name }}.Tests.OptionsTests

open Xunit

open {{ package_name }}

[<Fact>]
let ``no arguments means all figures and no files`` () =
    let options = Options.parse [||]

    Assert.Equal<Mode>(Mode.All, options.Mode)
    Assert.Empty options.Files
    Assert.Equal<Status>(Status.Ok, options.Status)

[<Fact>]
let ``help wins over everything after it`` () =
    let options = Options.parse [| "file.txt"; "--help"; "other.txt" |]

    Assert.Equal<Status>(Status.Help, options.Status)
    Assert.Equal<string list>([ "file.txt" ], options.Files)

[<Fact>]
let ``version is recognised`` () =
    let options = Options.parse [| "-V" |]

    Assert.Equal<Status>(Status.Version, options.Status)
    Assert.Equal("0.1.0", Options.Version)

[<Theory>]
[<InlineData("-l", "Lines")>]
[<InlineData("--words", "Words")>]
[<InlineData("-c", "Bytes")>]
let ``each mode flag selects one figure`` (flag: string) (expected: string) =
    let options = Options.parse [| flag |]
    let mode = match expected with
               | "Lines" -> Mode.Lines
               | "Words" -> Mode.Words
               | _ -> Mode.Bytes

    Assert.Equal<Mode>(mode, options.Mode)
    Assert.Equal<Status>(Status.Ok, options.Status)

[<Fact>]
let ``files keep their order`` () =
    let options = Options.parse [| "first.txt"; "second.txt" |]

    Assert.Equal<string list>([ "first.txt"; "second.txt" ], options.Files)

[<Fact>]
let ``two different modes are a usage error`` () =
    let options = Options.parse [| "-l"; "-w" |]

    Assert.Equal<Status>(Status.Error, options.Status)
    Assert.Contains("conflicts", options.Error)

[<Fact>]
let ``repeating the same mode is fine`` () =
    let options = Options.parse [| "-l"; "--lines" |]

    Assert.Equal<Status>(Status.Ok, options.Status)
    Assert.Equal<Mode>(Mode.Lines, options.Mode)

[<Fact>]
let ``an unknown option is a usage error`` () =
    let options = Options.parse [| "--bogus" |]

    Assert.Equal<Status>(Status.Error, options.Status)
    Assert.Contains("unknown option '--bogus'", options.Error)

[<Fact>]
let ``a double dash makes everything after it a file name`` () =
    let options = Options.parse [| "--"; "-l"; "--help" |]

    Assert.Equal<Status>(Status.Ok, options.Status)
    Assert.Equal<string list>([ "-l"; "--help" ], options.Files)

[<Fact>]
let ``a bare dash is a file name meaning standard input`` () =
    let options = Options.parse [| "-"; "-l" |]

    Assert.Equal<Status>(Status.Ok, options.Status)
    Assert.Equal<string list>([ "-" ], options.Files)
    Assert.Equal<Mode>(Mode.Lines, options.Mode)

[<Fact>]
let ``usage names the program and lists every flag`` () =
    let text = Options.usage "sample"

    Assert.StartsWith("usage: sample", text)
    Assert.Contains("--lines", text)
    Assert.Contains("--version", text)
    Assert.EndsWith("\n", text)

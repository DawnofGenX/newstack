module {{ package_name }}.Tests.CountsTests

open Xunit

open {{ package_name }}

[<Fact>]
let ``a file closed by a newline counts that line`` () =
    let counts = Counts.ofString "one two\nthree\n"

    Assert.Equal(2L, counts.Lines)
    Assert.Equal(3L, counts.Words)
    Assert.Equal(14L, counts.Bytes)

[<Fact>]
let ``a final unterminated line is not counted, and its bytes still are`` () =
    let counts = Counts.ofString "one two\nthree"

    Assert.Equal(1L, counts.Lines)
    Assert.Equal(3L, counts.Words)
    Assert.Equal(13L, counts.Bytes)

[<Fact>]
let ``empty text has no lines and no words`` () =
    let counts = Counts.ofString ""

    Assert.Equal<Counts>(Counts.zero, counts)

[<Fact>]
let ``runs of whitespace separate words without adding any`` () =
    let counts = Counts.ofString "  alpha\tbeta\r\ngamma  \n"

    Assert.Equal(2L, counts.Lines)
    Assert.Equal(3L, counts.Words)

[<Fact>]
let ``raw bytes win over the UTF-8 length of the decoded text`` () =
    // The caller passes the byte count it actually read, which is what wc reports.
    let counts = Counts.ofStringWithBytes 99L "alpha beta\n"

    Assert.Equal(1L, counts.Lines)
    Assert.Equal(2L, counts.Words)
    Assert.Equal(99L, counts.Bytes)

[<Fact>]
let ``ofBytes decodes UTF-8 and reports the raw length`` () =
    let counts = Counts.ofBytes ("caf\u00e9\n" |> System.Text.Encoding.UTF8.GetBytes)

    Assert.Equal(1L, counts.Lines)
    Assert.Equal(1L, counts.Words)
    Assert.Equal(6L, counts.Bytes)

[<Fact>]
let ``plus adds every figure`` () =
    let total = Counts.plus (Counts.ofString "a b\n") (Counts.ofString "c\n")

    Assert.Equal(2L, total.Lines)
    Assert.Equal(3L, total.Words)
    Assert.Equal(6L, total.Bytes)

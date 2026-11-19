using System.IO;
using Xunit;

namespace {{ package_name }}.Tests;

public class DiffTests
{
    [Fact]
    public void IdenticalTextsProduceNoChanges()
    {
        var out = new StringWriter();
        var err = new StringWriter();
        var code = Cli.Run(new[] { WriteTemp("a\nb\nc\n"), WriteTemp("a\nb\nc\n") }, TextReader.Null, out, err);
        Assert.Equal(0, code);
        Assert.Contains("--- a", out.ToString());
        Assert.Contains("+++ b", out.ToString());
    }

    [Fact]
    public void SingleLineChange()
    {
        var a = WriteTemp("a\nb\nc\n");
        var b = WriteTemp("a\nB\nc\n");
        var out = new StringWriter();
        var err = new StringWriter();
        var code = Cli.Run(new[] { a, b }, TextReader.Null, out, err);
        Assert.Equal(0, code);
        var s = out.ToString();
        Assert.Contains("-b", s);
        Assert.Contains("+B", s);
    }

    [Fact]
    public void DiffPureFunction()
    {
        var ops = Differ.Diff(new[] { "a", "b", "c" }, new[] { "a", "X", "c" });
        Assert.Equal(3, ops.Count);
        Assert.Equal((0, "a"), ops[0]);
        Assert.Equal((-1, "b"), ops[1]);
        Assert.Equal((1, "X"), ops[2]);
    }

    [Fact]
    public void MissingArgsReturnsUsageError()
    {
        var out = new StringWriter();
        var err = new StringWriter();
        var code = Cli.Run(new string[] { }, TextReader.Null, out, err);
        Assert.Equal(2, code);
    }

    [Fact]
    public void BadContextReturnsUsageError()
    {
        var a = WriteTemp("a\n");
        var b = WriteTemp("b\n");
        var out = new StringWriter();
        var err = new StringWriter();
        var code = Cli.Run(new[] { a, b, "--context", "x" }, TextReader.Null, out, err);
        Assert.Equal(2, code);
    }

    private static string WriteTemp(string content)
    {
        var p = Path.GetTempFileName();
        File.WriteAllText(p, content);
        return p;
    }
}

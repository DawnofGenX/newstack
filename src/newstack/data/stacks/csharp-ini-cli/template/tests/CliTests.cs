using Xunit;

namespace {{ package_name }}.Tests;

public class CliTests
{
    private static (int Code, string Out, string Err) Run(string[] args, string stdin = "")
    {
        TextWriter originalOut = Console.Out;
        TextWriter originalErr = Console.Error;
        TextReader originalIn = Console.In;
        var output = new StringWriter();
        var errors = new StringWriter();
        try
        {
            Console.SetOut(output);
            Console.SetError(errors);
            Console.SetIn(new StringReader(stdin));
            int code = Ini.Run(args);
            return (code, output.ToString(), errors.ToString());
        }
        finally
        {
            Console.SetOut(originalOut);
            Console.SetError(originalErr);
            Console.SetIn(originalIn);
        }
    }

    [Fact]
    public void HelpExitsZero()
    {
        var result = Run(new[] { "--help" });
        Assert.Equal(0, result.Code);
        Assert.Contains("Usage:", result.Out);
    }

    [Fact]
    public void PrintsJsonByDefault()
    {
        var result = Run(Array.Empty<string>(), "[server]\nport = 8080\n");
        Assert.Equal(0, result.Code);
        Assert.Contains("\"port\": \"8080\"", result.Out);
    }

    [Fact]
    public void GetsASingleValue()
    {
        var result = Run(new[] { "--get", "server.port" }, "[server]\nport = 8080\n");
        Assert.Equal(0, result.Code);
        Assert.Equal("8080", result.Out.Trim());
    }

    [Fact]
    public void UnknownKeyExitsOne()
    {
        var result = Run(new[] { "--get", "server.missing" }, "[server]\nport = 8080\n");
        Assert.Equal(1, result.Code);
        Assert.Contains("no such key", result.Err);
    }

    [Fact]
    public void ListsSections()
    {
        var result = Run(new[] { "--list-sections" }, "top = 1\n[a]\nx = 2\n");
        Assert.Equal(0, result.Code);
        Assert.Equal(new[] { "(default)", "a" }, result.Out.Split('\n', StringSplitOptions.RemoveEmptyEntries));
    }

    [Fact]
    public void WritesIniBack()
    {
        var result = Run(new[] { "--ini" }, "[a]\nx = 1\n");
        Assert.Equal(0, result.Code);
        Assert.Equal("[a]\nx = 1", result.Out.Trim());
    }

    [Fact]
    public void UnknownOptionExitsTwo()
    {
        var result = Run(new[] { "--bogus" });
        Assert.Equal(2, result.Code);
        Assert.Contains("unknown option --bogus", result.Err);
    }

    [Fact]
    public void MissingFileExitsOne()
    {
        var result = Run(new[] { "does-not-exist.ini" });
        Assert.Equal(1, result.Code);
    }

    [Fact]
    public void MalformedDocumentExitsOne()
    {
        var result = Run(Array.Empty<string>(), "not a pair\n");
        Assert.Equal(1, result.Code);
        Assert.Contains("line 1", result.Err);
    }
}

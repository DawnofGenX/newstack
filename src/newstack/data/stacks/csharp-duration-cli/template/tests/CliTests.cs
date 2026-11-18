using System.Globalization;
using Xunit;

public class CliTests
{
    private static (int Status, string Out, string Err) Invoke(params string[] argv)
    {
        var originalOut = Console.Out;
        var originalErr = Console.Error;
        var stdout = new StringWriter(CultureInfo.InvariantCulture);
        var stderr = new StringWriter(CultureInfo.InvariantCulture);
        Console.SetOut(stdout);
        Console.SetError(stderr);
        try
        {
            var status = Durations.Run(argv);
            return (status, stdout.ToString(), stderr.ToString());
        }
        finally
        {
            Console.SetOut(originalOut);
            Console.SetError(originalErr);
        }
    }

    [Fact]
    public void Parse_reports_seconds_iso_and_human()
    {
        var result = Invoke("parse", "1h30m");
        Assert.Equal(0, result.Status);
        Assert.Contains("seconds=5400", result.Out, StringComparison.Ordinal);
        Assert.Contains("iso=PT1H30M", result.Out, StringComparison.Ordinal);
        Assert.Contains("human=1h30m", result.Out, StringComparison.Ordinal);
    }

    [Fact]
    public void Add_reports_both_ends()
    {
        var result = Invoke("add", "P1D", "--from", "2026-01-31T23:30:00Z");
        Assert.Equal(0, result.Status);
        Assert.Contains("from=2026-01-31T23:30:00Z", result.Out, StringComparison.Ordinal);
        Assert.Contains("to=2026-02-01T23:30:00Z", result.Out, StringComparison.Ordinal);
    }

    [Fact]
    public void Between_reports_a_negative_difference_when_reversed()
    {
        var result = Invoke("between", "2026-01-02T00:00:00Z", "2026-01-01T00:00:00Z");
        Assert.Equal(0, result.Status);
        Assert.Contains("human=-1d", result.Out, StringComparison.Ordinal);
    }

    [Fact]
    public void A_bad_duration_exits_1()
    {
        var result = Invoke("parse", "next tuesday");
        Assert.Equal(1, result.Status);
        Assert.Contains("csharp-duration-cli:", result.Err, StringComparison.Ordinal);
    }

    [Fact]
    public void A_bad_timestamp_exits_1()
    {
        var result = Invoke("between", "2026-01-01T00:00:00Z", "yesterday");
        Assert.Equal(1, result.Status);
        Assert.Contains("not a timestamp", result.Err, StringComparison.Ordinal);
    }

    [Fact]
    public void An_unknown_command_exits_2()
    {
        var result = Invoke("frobnicate");
        Assert.Equal(2, result.Status);
        Assert.Contains("unknown command", result.Err, StringComparison.Ordinal);
    }

    [Fact]
    public void No_command_exits_2()
    {
        Assert.Equal(2, Invoke().Status);
    }

    [Fact]
    public void Help_exits_0()
    {
        var result = Invoke("--help");
        Assert.Equal(0, result.Status);
        Assert.Contains("Usage:", result.Out, StringComparison.Ordinal);
    }
}

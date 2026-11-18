using Xunit;

namespace {{ package_name }}.Tests;

public class CliTests
{
    private static (string Out, string Err, int Status) Capture(params string[] args)
    {
        var originalOut = Console.Out;
        var originalErr = Console.Error;
        using var output = new StringWriter();
        using var error = new StringWriter();
        Console.SetOut(output);
        Console.SetError(error);
        try
        {
            var status = Semver.Run(args);
            return (output.ToString(), error.ToString(), status);
        }
        finally
        {
            Console.SetOut(originalOut);
            Console.SetError(originalErr);
        }
    }

    [Fact]
    public void ParsePrintsTheComponents()
    {
        var result = Capture("parse", "1.2.3-rc.1");
        Assert.Equal(0, result.Status);
        Assert.Contains("major=1 minor=2 patch=3", result.Out);
        Assert.Contains("prerelease=rc.1", result.Out);
    }

    [Fact]
    public void ComparePrintsASign()
    {
        Assert.Equal("-1", Capture("compare", "1.0.0-alpha", "1.0.0").Out.Trim());
        Assert.Equal("0", Capture("compare", "1.0.0", "1.0.0+other").Out.Trim());
        Assert.Equal("1", Capture("compare", "2.0.0", "1.9.9").Out.Trim());
    }

    [Fact]
    public void BumpMovesTheRightComponent()
    {
        Assert.Equal("1.2.4", Capture("bump", "patch", "1.2.3").Out.Trim());
        Assert.Equal("1.3.0", Capture("bump", "minor", "1.2.3-beta.1").Out.Trim());
        Assert.Equal("2.0.0", Capture("bump", "major", "1.9.9").Out.Trim());
    }

    [Fact]
    public void SatisfiesExitsOneWhenTheRangeDoesNotMatch()
    {
        var matched = Capture("satisfies", "1.4.0", "^1.2.3");
        Assert.Equal(0, matched.Status);
        Assert.Equal("true", matched.Out.Trim());

        var missed = Capture("satisfies", "2.0.0", "^1.2.3");
        Assert.Equal(1, missed.Status);
        Assert.Equal("false", missed.Out.Trim());
    }

    [Fact]
    public void BadUsageExitsTwo()
    {
        Assert.Equal(2, Capture().Status);
        Assert.Equal(2, Capture("frobnicate").Status);
        Assert.Equal(2, Capture("parse").Status);
        Assert.Equal(2, Capture("bump", "sideways", "1.0.0").Status);
    }

    [Fact]
    public void InvalidVersionExitsOne()
    {
        var result = Capture("parse", "1.2");
        Assert.Equal(1, result.Status);
        Assert.Contains("version must be major.minor.patch", result.Err);
    }

    [Fact]
    public void HelpExitsZero()
    {
        var result = Capture("--help");
        Assert.Equal(0, result.Status);
        Assert.Contains("satisfies", result.Out);
    }
}

using Xunit;

namespace {{ package_name }}.Tests;

public class SemVersionTests
{
    [Theory]
    [InlineData("1.2.3", 1, 2, 3)]
    [InlineData("0.0.0", 0, 0, 0)]
    [InlineData("10.20.30", 10, 20, 30)]
    public void ParsesTheCoreTriple(string text, int major, int minor, int patch)
    {
        var version = SemVersion.Parse(text);
        Assert.Equal(major, version.Major);
        Assert.Equal(minor, version.Minor);
        Assert.Equal(patch, version.Patch);
    }

    [Fact]
    public void SplitsPrereleaseAndBuild()
    {
        var version = SemVersion.Parse("1.2.3-beta.1+exp.sha.5114f85");
        Assert.Equal("beta.1", version.Prerelease);
        Assert.Equal("exp.sha.5114f85", version.Build);
        Assert.True(version.IsPrerelease);
    }

    [Fact]
    public void BuildMetadataIsIgnoredByComparisons()
    {
        Assert.Equal(0, SemVersion.Parse("1.2.3+build.1").CompareTo(SemVersion.Parse("1.2.3+build.2")));
    }

    [Theory]
    [InlineData("1.0.0-alpha", "1.0.0", -1)]
    [InlineData("1.0.0-alpha", "1.0.0-alpha.1", -1)]
    [InlineData("1.0.0-alpha.1", "1.0.0-alpha.beta", -1)]
    [InlineData("1.0.0-beta.2", "1.0.0-beta.11", -1)]
    [InlineData("1.0.0-rc.1", "1.0.0", -1)]
    [InlineData("1.0.0", "2.0.0", -1)]
    [InlineData("1.1.0", "1.0.9", 1)]
    public void OrdersTheWaySemverRequires(string left, string right, int expected)
    {
        Assert.Equal(expected, Math.Sign(SemVersion.Parse(left).CompareTo(SemVersion.Parse(right))));
    }

    [Theory]
    [InlineData("")]
    [InlineData("1")]
    [InlineData("1.2")]
    [InlineData("1.2.3.4")]
    [InlineData("01.2.3")]
    [InlineData("1.2.x")]
    [InlineData("1.2.3-")]
    [InlineData("1.2.3-alpha..1")]
    public void RejectsMalformedVersions(string text)
    {
        Assert.Throws<FormatException>(() => SemVersion.Parse(text));
        Assert.False(SemVersion.TryParse(text, out _));
    }

    [Fact]
    public void RoundTripsThroughToString()
    {
        const string text = "1.2.3-beta.1+build.5";
        Assert.Equal(text, SemVersion.Parse(text).ToString());
    }
}

using Xunit;

namespace {{ package_name }}.Tests;

public class RangesTests
{
    [Theory]
    [InlineData("1.2.3", "1.2.3", true)]
    [InlineData("1.2.3", "=1.2.3", true)]
    [InlineData("1.2.4", "1.2.3", false)]
    [InlineData("1.3.0", ">1.2.3", true)]
    [InlineData("1.2.3", ">=1.2.3", true)]
    [InlineData("1.2.2", "<1.2.3", true)]
    [InlineData("1.2.3", "<=1.2.3", true)]
    public void ComparesWithExplicitOperators(string version, string range, bool expected)
    {
        Assert.Equal(expected, Ranges.Satisfies(SemVersion.Parse(version), range));
    }

    [Theory]
    [InlineData("1.9.9", "^1.2.3", true)]
    [InlineData("2.0.0", "^1.2.3", false)]
    [InlineData("1.2.2", "^1.2.3", false)]
    [InlineData("0.2.9", "^0.2.3", true)]
    [InlineData("0.3.0", "^0.2.3", false)]
    [InlineData("0.0.3", "^0.0.3", true)]
    [InlineData("0.0.4", "^0.0.3", false)]
    public void CaretAllowsTheCompatibleWindow(string version, string range, bool expected)
    {
        Assert.Equal(expected, Ranges.Satisfies(SemVersion.Parse(version), range));
    }

    [Theory]
    [InlineData("1.2.9", "~1.2.3", true)]
    [InlineData("1.3.0", "~1.2.3", false)]
    [InlineData("1.2.0", "~1.2", true)]
    [InlineData("1.9.0", "~1", true)]
    [InlineData("2.0.0", "~1", false)]
    public void TildeAllowsPatchAndMinorDrift(string version, string range, bool expected)
    {
        Assert.Equal(expected, Ranges.Satisfies(SemVersion.Parse(version), range));
    }

    [Theory]
    [InlineData("1.4.0", "1.x", true)]
    [InlineData("2.0.0", "1.x", false)]
    [InlineData("1.2.7", "1.2.*", true)]
    [InlineData("1.3.0", "1.2.*", false)]
    [InlineData("0.0.1", "*", true)]
    [InlineData("1.0.0-rc.1", "*", false)]
    public void WildcardsAndStar(string version, string range, bool expected)
    {
        Assert.Equal(expected, Ranges.Satisfies(SemVersion.Parse(version), range));
    }

    [Fact]
    public void RejectsAnUnreadableRange()
    {
        Assert.Throws<FormatException>(() => Ranges.Satisfies(SemVersion.Parse("1.0.0"), "1.0.0 - 2.0.0"));
    }
}

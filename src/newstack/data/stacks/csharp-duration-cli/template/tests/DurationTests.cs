using System.Globalization;
using Xunit;

public class DurationTests
{
    [Theory]
    [InlineData("P1D", 86400)]
    [InlineData("P1W", 604800)]
    [InlineData("PT45S", 45)]
    [InlineData("PT1H30M", 5400)]
    [InlineData("P2DT3H4M5S", 183845)]
    [InlineData("P0D", 0)]
    [InlineData("PT0S", 0)]
    public void It_parses_iso_durations(string text, double seconds)
    {
        Assert.Equal(seconds, IsoDuration.ParseIso(text).TotalSeconds);
    }

    [Theory]
    [InlineData("1h30m", 5400)]
    [InlineData("2d", 172800)]
    [InlineData("-45s", -45)]
    [InlineData("1d 12h", 129600)]
    [InlineData("90m", 5400)]
    [InlineData("0s", 0)]
    public void It_parses_human_durations(string text, double seconds)
    {
        Assert.Equal(seconds, IsoDuration.ParseHuman(text).TotalSeconds);
    }

    [Theory]
    [InlineData("P1Y")]
    [InlineData("P2M")]
    [InlineData("PT")]
    [InlineData("P")]
    [InlineData("")]
    [InlineData("1h30")]
    [InlineData("soon")]
    public void It_rejects_unusable_input(string text)
    {
        Assert.ThrowsAny<Exception>(() => IsoDuration.Parse(text));
    }

    [Fact]
    public void Calendar_months_are_refused_with_a_reason()
    {
        var error = Assert.Throws<FormatException>(() => IsoDuration.ParseIso("P3M"));
        Assert.Contains("ambiguous", error.Message, StringComparison.Ordinal);
    }

    [Theory]
    [InlineData(86400, "P1D")]
    [InlineData(5400, "PT1H30M")]
    [InlineData(45, "PT45S")]
    [InlineData(0, "P0D")]
    [InlineData(-1800, "-PT30M")]
    [InlineData(183845, "P2DT3H4M5S")]
    public void It_formats_iso_round_trip_ready(double seconds, string expected)
    {
        Assert.Equal(expected, IsoDuration.FromSeconds(seconds).ToIso());
    }

    [Theory]
    [InlineData(86400, "1d")]
    [InlineData(5400, "1h30m")]
    [InlineData(129600, "1d12h")]
    [InlineData(-45, "-45s")]
    [InlineData(0, "0s")]
    public void It_formats_human(double seconds, string expected)
    {
        Assert.Equal(expected, IsoDuration.FromSeconds(seconds).ToHuman());
    }

    [Fact]
    public void Formatting_then_parsing_returns_the_same_duration()
    {
        foreach (var seconds in new[] { 0d, 1, 59, 60, 3600, 90061, -7200 })
        {
            var original = IsoDuration.FromSeconds(seconds);
            var reparsed = IsoDuration.ParseIso(original.ToIso());
            Assert.Equal(original.Value, reparsed.Value);
        }
    }

    [Fact]
    public void Adding_crosses_a_month_boundary()
    {
        var from = DateTimeOffset.Parse("2026-01-31T23:30:00Z", CultureInfo.InvariantCulture);
        var result = IsoDuration.ParseIso("PT1H").AddTo(from);
        Assert.Equal("2026-02-01T00:30:00Z", result.UtcDateTime.ToString("yyyy-MM-ddTHH:mm:ssZ", CultureInfo.InvariantCulture));
    }

    [Fact]
    public void Negative_durations_subtract()
    {
        var from = DateTimeOffset.Parse("2026-03-01T00:00:00Z", CultureInfo.InvariantCulture);
        var result = IsoDuration.ParseHuman("-1d").AddTo(from);
        Assert.Equal(new DateTimeOffset(2026, 2, 28, 0, 0, 0, TimeSpan.Zero), result);
    }

    [Fact]
    public void Fractions_are_supported_in_the_human_form()
    {
        Assert.Equal(90, IsoDuration.ParseHuman("1.5m").TotalSeconds);
    }
}

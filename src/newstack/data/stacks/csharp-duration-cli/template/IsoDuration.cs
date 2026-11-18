using System.Globalization;
using System.Text.RegularExpressions;

/// <summary>
/// An ISO 8601 duration (the <c>P</c> format) plus the terse human spelling
/// people actually type. Values are held as a <see cref="TimeSpan"/>, so
/// arithmetic uses the same clock as <see cref="DateTimeOffset"/>.
///
/// Calendar years and months are refused on purpose: a "month" is 28 to 31
/// days, so silently picking a number would make <c>add</c> wrong twice a year.
/// </summary>
public sealed class IsoDuration
{
    private static readonly Regex IsoPattern = new(
        @"^(?<sign>[-+])?P(?:(?<weeks>[0-9]+)W)?(?:(?<days>[0-9]+)D)?(?:(?:T(?:(?<hours>[0-9]+)H)?(?:(?<minutes>[0-9]+)M)?(?:(?<seconds>[0-9]+)S)?))?$",
        RegexOptions.CultureInvariant);

    private static readonly Regex HumanPattern = new(
        @"^(?<sign>[-+])?(?:(?<value>[0-9]+(?:\.[0-9]+)?)\s*(?<unit>[dhms]))+\s*$",
        RegexOptions.CultureInvariant | RegexOptions.IgnoreCase);

    private static readonly Regex HumanAtom = new(
        @"(?<value>[0-9]+(?:\.[0-9]+)?)\s*(?<unit>[dhms])",
        RegexOptions.CultureInvariant | RegexOptions.IgnoreCase);

    public IsoDuration(TimeSpan value) => Value = value;

    public TimeSpan Value { get; }

    public static IsoDuration FromSeconds(double seconds) => new(TimeSpan.FromSeconds(seconds));

    /// <summary>Parses <c>P1W</c>, <c>P2DT3H4M5S</c>, <c>PT45S</c>, <c>P0D</c>.</summary>
    public static IsoDuration ParseIso(string text)
    {
        ArgumentNullException.ThrowIfNull(text);

        var trimmed = text.Trim();
        if (trimmed.Length == 0)
        {
            throw new FormatException("duration is empty");
        }

        // Anything before the T is a date component; Y and M there are calendar
        // units, which this type refuses to guess at.
        var timeIndex = trimmed.IndexOf('T');
        var datePart = timeIndex >= 0 ? trimmed[..timeIndex] : trimmed;
        if (datePart.Contains('Y') || datePart.Contains('M'))
        {
            throw new FormatException("calendar years and months are ambiguous; express them as weeks or days");
        }

        var match = IsoPattern.Match(trimmed);
        var body = match.Success ? trimmed.TrimStart('-', '+') : trimmed;
        if (match.Success is false || body is "P" or "PT")
        {
            throw new FormatException($"not an ISO 8601 duration: {text}");
        }

        var value = TimeSpan.Zero;
        value += TimeSpan.FromDays(Whole(match, "weeks") * 7);
        value += TimeSpan.FromDays(Whole(match, "days"));
        value += TimeSpan.FromHours(Whole(match, "hours"));
        value += TimeSpan.FromMinutes(Whole(match, "minutes"));
        value += TimeSpan.FromSeconds(Whole(match, "seconds"));
        return new IsoDuration(match.Groups["sign"].Value == "-" ? -value : value);
    }

    /// <summary>Parses <c>1h30m</c>, <c>2d</c>, <c>-45s</c>, <c>1d 12h</c>.</summary>
    public static IsoDuration ParseHuman(string text)
    {
        ArgumentNullException.ThrowIfNull(text);

        var trimmed = text.Trim();
        if (trimmed.Length == 0)
        {
            throw new FormatException("duration is empty");
        }

        if (HumanPattern.IsMatch(trimmed) is false)
        {
            throw new FormatException($"not a duration like 1h30m: {text}");
        }

        var negative = trimmed.StartsWith('-');
        var total = TimeSpan.Zero;
        foreach (Match atom in HumanAtom.Matches(trimmed))
        {
            var amount = double.Parse(atom.Groups["value"].Value, CultureInfo.InvariantCulture);
            total += char.ToLowerInvariant(atom.Groups["unit"].Value[0]) switch
            {
                'd' => TimeSpan.FromDays(amount),
                'h' => TimeSpan.FromHours(amount),
                'm' => TimeSpan.FromMinutes(amount),
                's' => TimeSpan.FromSeconds(amount),
                _ => throw new FormatException($"unknown unit: {atom.Groups["unit"].Value}"),
            };
        }

        return new IsoDuration(negative ? -total : total);
    }

    /// <summary>Re-parses text, accepting either spelling.</summary>
    public static IsoDuration Parse(string text) =>
        text.TrimStart().StartsWith('P') || text.TrimStart().StartsWith("-P")
            ? ParseIso(text)
            : ParseHuman(text);

    public DateTimeOffset AddTo(DateTimeOffset from) => from + Value;

    public double TotalSeconds => Value.TotalSeconds;

    /// <summary>Canonical ISO form: <c>P2DT3H</c>, <c>PT45S</c>, <c>P0D</c>, <c>-PT30M</c>.</summary>
    public string ToIso()
    {
        if (Value == TimeSpan.Zero)
        {
            return "P0D";
        }

        var sign = Value < TimeSpan.Zero ? "-" : string.Empty;
        var value = Value.Duration();
        var days = value.Days;
        var time = string.Concat(
            value.Hours > 0 ? $"{value.Hours}H" : string.Empty,
            value.Minutes > 0 ? $"{value.Minutes}M" : string.Empty,
            value.Seconds > 0 || (value.Hours == 0 && value.Minutes == 0) ? $"{value.Seconds}S" : string.Empty);

        var date = days > 0 ? $"{days}D" : string.Empty;
        return $"{sign}P{date}{(time.Length > 0 ? "T" + time : string.Empty)}";
    }

    /// <summary>Terse human form, largest unit first: <c>2d4h</c>, <c>1h30m</c>, <c>45s</c>.</summary>
    public string ToHuman()
    {
        if (Value == TimeSpan.Zero)
        {
            return "0s";
        }

        var sign = Value < TimeSpan.Zero ? "-" : string.Empty;
        var value = Value.Duration();
        var parts = new List<string>();

        if (value.Days > 0) parts.Add($"{value.Days}d");
        if (value.Hours > 0) parts.Add($"{value.Hours}h");
        if (value.Minutes > 0) parts.Add($"{value.Minutes}m");
        if (value.Seconds > 0 || parts.Count == 0) parts.Add($"{value.Seconds}s");

        return sign + string.Concat(parts);
    }

    public override string ToString() => ToIso();

    private static int Whole(Match match, string group)
    {
        var captured = match.Groups[group];
        return captured.Success ? int.Parse(captured.Value, CultureInfo.InvariantCulture) : 0;
    }
}

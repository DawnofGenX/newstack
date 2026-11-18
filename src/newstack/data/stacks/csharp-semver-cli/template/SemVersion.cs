using System.Globalization;

namespace {{ package_name }};

/// <summary>Semantic Version 2.0.0: parse, order and match against a range.</summary>
public sealed class SemVersion : IComparable<SemVersion>, IEquatable<SemVersion>
{
    public SemVersion(int major, int minor, int patch, string? prerelease = null, string? build = null)
    {
        Major = major;
        Minor = minor;
        Patch = patch;
        Prerelease = prerelease ?? string.Empty;
        Build = build ?? string.Empty;
    }

    public int Major { get; }

    public int Minor { get; }

    public int Patch { get; }

    /// <summary>Everything after the first '-', empty when the version is a release.</summary>
    public string Prerelease { get; }

    /// <summary>Everything after the first '+'; ignored by every comparison.</summary>
    public string Build { get; }

    public bool IsPrerelease => Prerelease.Length > 0;

    public static SemVersion Parse(string text)
    {
        if (string.IsNullOrWhiteSpace(text))
        {
            throw new FormatException("version is empty");
        }

        var trimmed = text.Trim();
        var withoutBuild = trimmed;
        var build = string.Empty;
        var plus = withoutBuild.IndexOf('+', StringComparison.Ordinal);
        if (plus >= 0)
        {
            build = withoutBuild[(plus + 1)..];
            withoutBuild = withoutBuild[..plus];
            ValidateIdentifiers(build, "build metadata");
        }

        var prerelease = string.Empty;
        var core = withoutBuild;
        var dash = withoutBuild.IndexOf('-', StringComparison.Ordinal);
        if (dash >= 0)
        {
            prerelease = withoutBuild[(dash + 1)..];
            core = withoutBuild[..dash];
        }

        var parts = core.Split('.');
        if (parts.Length != 3)
        {
            throw new FormatException($"version must be major.minor.patch: \"{text}\"");
        }

        var numbers = new int[3];
        for (var i = 0; i < 3; i += 1)
        {
            numbers[i] = ParseNumber(parts[i], text);
        }

        if (prerelease.Length > 0)
        {
            ValidateIdentifiers(prerelease, "prerelease");
        }

        return new SemVersion(numbers[0], numbers[1], numbers[2], prerelease, build);
    }

    public static bool TryParse(string text, out SemVersion version)
    {
        try
        {
            version = Parse(text);
            return true;
        }
        catch (FormatException)
        {
            version = new SemVersion(0, 0, 0);
            return false;
        }
    }

    private static int ParseNumber(string piece, string whole)
    {
        if (piece.Length == 0)
        {
            throw new FormatException($"missing version component in \"{whole}\"");
        }

        if (piece.Length > 1 && piece[0] == '0')
        {
            throw new FormatException($"leading zero in \"{whole}\"");
        }

        foreach (var character in piece)
        {
            if (!char.IsAsciiDigit(character))
            {
                throw new FormatException($"version components must be numbers: \"{whole}\"");
            }
        }

        return int.Parse(piece, CultureInfo.InvariantCulture);
    }

    private static void ValidateIdentifiers(string value, string what)
    {
        foreach (var identifier in value.Split('.'))
        {
            if (identifier.Length == 0)
            {
                throw new FormatException($"empty {what} identifier");
            }

            foreach (var character in identifier)
            {
                if (!char.IsAsciiLetterOrDigit(character) && character != '-')
                {
                    throw new FormatException($"invalid character '{character}' in {what}");
                }
            }

            if (identifier.Length > 1 && identifier[0] == '0' && identifier.All(char.IsAsciiDigit))
            {
                throw new FormatException($"leading zero in {what} identifier \"{identifier}\"");
            }
        }
    }

    public int CompareTo(SemVersion? other)
    {
        if (other is null)
        {
            return 1;
        }

        var core = Major.CompareTo(other.Major);
        if (core != 0)
        {
            return core;
        }

        core = Minor.CompareTo(other.Minor);
        if (core != 0)
        {
            return core;
        }

        core = Patch.CompareTo(other.Patch);
        if (core != 0)
        {
            return core;
        }

        if (!IsPrerelease && !other.IsPrerelease)
        {
            return 0;
        }

        if (!IsPrerelease)
        {
            return 1;
        }

        if (!other.IsPrerelease)
        {
            return -1;
        }

        return ComparePrerelease(Prerelease, other.Prerelease);
    }

    private static int ComparePrerelease(string left, string right)
    {
        var a = left.Split('.');
        var b = right.Split('.');
        for (var i = 0; i < Math.Min(a.Length, b.Length); i += 1)
        {
            var leftNumeric = a[i].All(char.IsAsciiDigit);
            var rightNumeric = b[i].All(char.IsAsciiDigit);
            int step;
            if (leftNumeric && rightNumeric)
            {
                step = long.Parse(a[i], CultureInfo.InvariantCulture)
                    .CompareTo(long.Parse(b[i], CultureInfo.InvariantCulture));
            }
            else if (leftNumeric)
            {
                step = -1;
            }
            else if (rightNumeric)
            {
                step = 1;
            }
            else
            {
                step = string.CompareOrdinal(a[i], b[i]);
            }

            if (step != 0)
            {
                return step < 0 ? -1 : 1;
            }
        }

        return a.Length.CompareTo(b.Length);
    }

    public bool Equals(SemVersion? other) => other is not null && CompareTo(other) == 0;

    public override bool Equals(object? obj) => obj is SemVersion other && Equals(other);

    public override int GetHashCode() => HashCode.Combine(Major, Minor, Patch, Prerelease);

    public override string ToString()
    {
        var text = $"{Major}.{Minor}.{Patch}";
        if (IsPrerelease)
        {
            text += "-" + Prerelease;
        }

        if (Build.Length > 0)
        {
            text += "+" + Build;
        }

        return text;
    }
}

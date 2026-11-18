using System.Globalization;

namespace {{ package_name }};

/// <summary>
/// Range matching: comparison operators, caret (compatible-with), tilde and
/// `x` wildcards. One range per call; `1.x` style partials expand to a
/// half-open interval the way npm's semver does it.
/// </summary>
public static class Ranges
{
    public static bool Satisfies(SemVersion version, string range)
    {
        var text = range.Trim();
        if (text.Length == 0)
        {
            throw new FormatException("range is empty");
        }

        if (text == "*" || text.Equals("latest", StringComparison.OrdinalIgnoreCase))
        {
            return !version.IsPrerelease;
        }

        foreach (var (op, operand) in Split(text))
        {
            if (!Matches(version, op, operand))
            {
                return false;
            }
        }

        return true;
    }

    private static IEnumerable<(string Op, string Operand)> Split(string text)
    {
        var operators = new[] { ">=", "<=", ">", "<", "=", "^", "~" };
        var op = "=";
        var rest = text;
        foreach (var candidate in operators)
        {
            if (!rest.StartsWith(candidate, StringComparison.Ordinal))
            {
                continue;
            }

            op = candidate;
            rest = rest[candidate.Length..].Trim();
            break;
        }

        if (op == "=" && rest.Contains(' ', StringComparison.Ordinal))
        {
            throw new FormatException($"expected a single range, got \"{text}\"");
        }

        yield return (op, rest);
    }

    private static bool Matches(SemVersion version, string op, string operand)
    {
        if (operand.Contains('x', StringComparison.OrdinalIgnoreCase)
            || operand.Contains('*', StringComparison.Ordinal))
        {
            return MatchesWildcard(version, operand);
        }

        var target = ParsePartial(operand);
        return op switch
        {
            "=" => version.CompareTo(target) == 0,
            ">" => version.CompareTo(target) > 0,
            ">=" => version.CompareTo(target) >= 0,
            "<" => version.CompareTo(target) < 0,
            "<=" => version.CompareTo(target) <= 0,
            "^" => version.CompareTo(target) >= 0 && version.CompareTo(CaretUpper(target)) < 0,
            "~" => version.CompareTo(target) >= 0 && version.CompareTo(TildeUpper(target, operand)) < 0,
            _ => throw new FormatException($"unknown operator \"{op}\""),
        };
    }

    private static SemVersion CaretUpper(SemVersion target)
    {
        if (target.Major > 0)
        {
            return new SemVersion(target.Major + 1, 0, 0);
        }

        if (target.Minor > 0)
        {
            return new SemVersion(0, target.Minor + 1, 0);
        }

        return new SemVersion(0, 0, target.Patch + 1);
    }

    private static SemVersion TildeUpper(SemVersion target, string operand)
    {
        // `~1` means "any 1.x", `~1.2` and `~1.2.3` mean "any 1.2.x".
        var pieces = operand.Split('-')[0].TrimStart('v').Split('.');
        return pieces.Length <= 1
            ? new SemVersion(target.Major + 1, 0, 0)
            : new SemVersion(target.Major, target.Minor + 1, 0);
    }

    private static bool MatchesWildcard(SemVersion version, string operand)
    {
        var pieces = operand.TrimStart('v').Split('.');
        var numbers = new List<int>();
        foreach (var piece in pieces)
        {
            var cleaned = piece.Trim();
            if (cleaned.Length == 0
                || cleaned.Equals("x", StringComparison.OrdinalIgnoreCase)
                || cleaned == "*")
            {
                break;
            }

            numbers.Add(int.Parse(cleaned, CultureInfo.InvariantCulture));
        }

        for (var i = 0; i < numbers.Count; i += 1)
        {
            var actual = i == 0 ? version.Major : i == 1 ? version.Minor : version.Patch;
            if (actual != numbers[i])
            {
                return false;
            }
        }

        return numbers.Count > 0;
    }

    private static SemVersion ParsePartial(string operand)
    {
        var pieces = operand.TrimStart('v').Split('.');
        var numbers = new int[3];
        for (var i = 0; i < 3; i += 1)
        {
            if (i >= pieces.Length)
            {
                numbers[i] = 0;
                continue;
            }

            var piece = pieces[i];
            var prerelease = string.Empty;
            var dash = piece.IndexOf('-', StringComparison.Ordinal);
            if (dash >= 0)
            {
                prerelease = piece[dash..];
                piece = piece[..dash];
            }

            if (!int.TryParse(piece, NumberStyles.None, CultureInfo.InvariantCulture, out numbers[i]))
            {
                throw new FormatException($"cannot read version \"{operand}\"");
            }

            if (prerelease.Length > 0)
            {
                return new SemVersion(numbers[0], numbers[1], numbers[2], prerelease[1..]);
            }
        }

        return new SemVersion(numbers[0], numbers[1], numbers[2]);
    }
}

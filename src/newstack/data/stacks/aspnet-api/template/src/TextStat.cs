using System.Text;
using System.Text.RegularExpressions;

namespace {{ package_name }};

/// <summary>
/// Counts text the way <c>wc</c> does: newlines for lines, runs of non-whitespace for
/// words, UTF-8 bytes for bytes. Pure: no I/O, no framework types, so tests drive it
/// directly and the endpoint stays a thin serializer.
/// </summary>
public static partial class TextStat
{
    public static Counts Of(string text)
    {
        ArgumentNullException.ThrowIfNull(text);

        return new Counts(
            Lines: text.Count(character => character == '\n'),
            Words: WordRuns().Matches(text).Count,
            Bytes: Encoding.UTF8.GetByteCount(text));
    }

    [GeneratedRegex(@"\S+")]
    private static partial Regex WordRuns();
}

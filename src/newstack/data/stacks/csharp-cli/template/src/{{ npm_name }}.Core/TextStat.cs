using System.Text;

namespace {{ package_name }};

/// <summary>Pure counting logic, with no I/O so tests drive it directly.</summary>
public static class TextStat
{
    /// <summary>Counts the raw bytes, and decodes them as UTF-8 to count lines and words.</summary>
    public static Counts Count(ReadOnlySpan<byte> data) =>
        Count(Encoding.UTF8.GetString(data), data.Length);

    /// <summary>Convenience overload for callers that already hold text.</summary>
    public static Counts Count(string text) =>
        Count(text, Encoding.UTF8.GetByteCount(text));

    /// <summary>
    /// A line is counted when a newline closes it, so a final unterminated line is not
    /// one; a word is a run of non-whitespace characters.
    /// </summary>
    private static Counts Count(string text, long bytes)
    {
        long lines = 0;
        long words = 0;
        bool inWord = false;

        foreach (char current in text)
        {
            if (current == '\n')
            {
                lines++;
            }

            if (char.IsWhiteSpace(current))
            {
                inWord = false;
            }
            else if (!inWord)
            {
                inWord = true;
                words++;
            }
        }

        return new Counts(lines, words, bytes);
    }
}

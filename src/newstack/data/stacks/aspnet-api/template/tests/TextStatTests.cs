using {{ package_name }};

namespace {{ package_name }}.Tests;

public sealed class TextStatTests
{
    [Theory]
    [InlineData("", 0, 0, 0)]
    [InlineData("one two\n", 1, 2, 8)]
    [InlineData("one two\nthree\n", 2, 3, 14)]
    [InlineData("  padded  \n", 1, 1, 11)]
    [InlineData("no trailing newline", 0, 3, 19)]
    [InlineData("h\u00e9llo w\u00f6rld\n", 1, 2, 14)]
    public void Counts_match_wc(string text, int lines, int words, int bytes)
    {
        Assert.Equal(new Counts(lines, words, bytes), TextStat.Of(text));
    }

    [Fact]
    public void Blank_lines_still_count_as_lines()
    {
        Assert.Equal(new Counts(3, 1, 4), TextStat.Of("\n\nx\n"));
    }

    [Fact]
    public void Whitespace_only_text_has_no_words_but_keeps_its_bytes()
    {
        Assert.Equal(new Counts(0, 0, 4), TextStat.Of("  \t "));
    }
}

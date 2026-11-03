using Xunit;

namespace {{ package_name }}.Tests;

public sealed class TextStatTests
{
    [Fact]
    public void EmptyInputCountsNothing()
    {
        Assert.Equal(new Counts(0, 0, 0), TextStat.Count(Array.Empty<byte>()));
    }

    [Fact]
    public void TrailingNewlineClosesTheLastLine()
    {
        Counts counts = TextStat.Count("one two\nthree\n");

        Assert.Equal(2, counts.Lines);
        Assert.Equal(3, counts.Words);
        Assert.Equal(14, counts.Bytes);
    }

    [Fact]
    public void FinalLineWithoutNewlineIsNotALine()
    {
        Counts counts = TextStat.Count("alpha beta");

        Assert.Equal(0, counts.Lines);
        Assert.Equal(2, counts.Words);
        Assert.Equal(10, counts.Bytes);
    }

    [Fact]
    public void RunsOfSpacesAndTabsAreOneWordBoundary()
    {
        Counts counts = TextStat.Count("a  b\tc\r\nd");

        Assert.Equal(4, counts.Words);
        Assert.Equal(1, counts.Lines);
    }

    [Fact]
    public void BytesAreCountedOnTheUtf8Encoding()
    {
        Counts counts = TextStat.Count("h\u00e9llo\n");

        Assert.Equal(1, counts.Lines);
        Assert.Equal(1, counts.Words);
        Assert.Equal(7, counts.Bytes);
    }

    [Fact]
    public void FiguresAddUpForAMultiFileTotal()
    {
        Counts total = TextStat.Count("a b\n").Plus(TextStat.Count("c\n"));

        Assert.Equal(new Counts(2, 3, 6), total);
    }
}

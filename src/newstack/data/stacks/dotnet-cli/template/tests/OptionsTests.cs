namespace {{ package_name }}.Tests;

public sealed class OptionsTests
{
    [Fact]
    public void NoArgumentsMeansAllFiguresAndNoFiles()
    {
        Options options = Options.Parse(Array.Empty<string>());

        Assert.Equal(Status.Ok, options.Status);
        Assert.True(options.Lines);
        Assert.True(options.Words);
        Assert.True(options.Bytes);
        Assert.Empty(options.Files);
    }

    [Fact]
    public void LinesFlagSelectsOnlyLines()
    {
        Options options = Options.Parse(new[] { "-l" });

        Assert.Equal(Status.Ok, options.Status);
        Assert.True(options.Lines);
        Assert.False(options.Words);
        Assert.False(options.Bytes);
    }

    [Fact]
    public void WordsFlagSelectsOnlyWords()
    {
        Options options = Options.Parse(new[] { "-w" });

        Assert.Equal(Status.Ok, options.Status);
        Assert.False(options.Lines);
        Assert.True(options.Words);
        Assert.False(options.Bytes);
    }

    [Fact]
    public void BytesFlagSelectsOnlyBytes()
    {
        Options options = Options.Parse(new[] { "-c" });

        Assert.Equal(Status.Ok, options.Status);
        Assert.False(options.Lines);
        Assert.False(options.Words);
        Assert.True(options.Bytes);
    }

    [Fact]
    public void LongFormFlagsAreRecognised()
    {
        Assert.True(Options.Parse(new[] { "--lines" }).Lines);
        Assert.True(Options.Parse(new[] { "--words" }).Words);
        Assert.True(Options.Parse(new[] { "--bytes" }).Bytes);
    }

    [Fact]
    public void FlagsAreAdditiveLikeWc()
    {
        Options options = Options.Parse(new[] { "-l", "-w", "-c" });

        Assert.Equal(Status.Ok, options.Status);
        Assert.True(options.Lines);
        Assert.True(options.Words);
        Assert.True(options.Bytes);
    }

    [Fact]
    public void APartialFlagCombinationSelectsOnlyThoseFigures()
    {
        Options options = Options.Parse(new[] { "-l", "-c" });

        Assert.Equal(Status.Ok, options.Status);
        Assert.True(options.Lines);
        Assert.False(options.Words);
        Assert.True(options.Bytes);
    }

    [Fact]
    public void HelpIsRecognised()
    {
        Assert.Equal(Status.Help, Options.Parse(new[] { "--help" }).Status);
        Assert.Equal(Status.Help, Options.Parse(new[] { "-h" }).Status);
    }

    [Fact]
    public void VersionIsRecognised()
    {
        Assert.Equal(Status.Version, Options.Parse(new[] { "--version" }).Status);
        Assert.Equal(Status.Version, Options.Parse(new[] { "-V" }).Status);
    }

    [Fact]
    public void AnUnknownOptionIsAnError()
    {
        Options options = Options.Parse(new[] { "--bogus" });

        Assert.Equal(Status.Error, options.Status);
        Assert.Contains("unknown option", options.Error, StringComparison.Ordinal);
    }

    [Fact]
    public void FilesAreCollectedInOrder()
    {
        Options options = Options.Parse(new[] { "-w", "a.txt", "b.txt" });

        Assert.Equal(Status.Ok, options.Status);
        Assert.Equal(new[] { "a.txt", "b.txt" }, options.Files);
    }

    [Fact]
    public void ADashIsTheStdinFile()
    {
        Options options = Options.Parse(new[] { "-" });

        Assert.Equal(Status.Ok, options.Status);
        Assert.Equal(new[] { "-" }, options.Files);
    }

    [Fact]
    public void DoubleDashMakesEverythingAfterAFile()
    {
        Options options = Options.Parse(new[] { "--", "-l" });

        Assert.Equal(Status.Ok, options.Status);
        Assert.Equal(new[] { "-l" }, options.Files);
    }
}

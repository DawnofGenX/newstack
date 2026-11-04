namespace {{ package_name }}.Tests;

public sealed class CliTests
{
    private readonly StringWriter _out = new();
    private readonly StringWriter _err = new();

    private int Run(string stdin, params string[] args) =>
        new Cli(new StringReader(stdin), "sample").Run(args, _out, _err);

    private string Stdout() => _out.ToString();

    private string Stderr() => _err.ToString();

    [Fact]
    public void HelpPrintsUsageAndExitsZero()
    {
        Assert.Equal(0, Run(string.Empty, "--help"));
        Assert.StartsWith("usage:", Stdout());
    }

    [Fact]
    public void VersionPrintsTheVersionAndExitsZero()
    {
        Assert.Equal(0, Run(string.Empty, "--version"));
        Assert.Equal(Options.Version, Stdout().Trim());
    }

    [Fact]
    public void WithNoFileStdinIsCountedAndAllThreeFiguresArePrinted()
    {
        Assert.Equal(0, Run("one two\nthree\n"));
        Assert.Equal("2       3      14", Stdout().Trim());
    }

    [Fact]
    public void AModeFlagPrintsOneFigurePerFile()
    {
        string file = Path.Combine(Path.GetTempPath(), Path.GetRandomFileName());
        File.WriteAllText(file, "alpha beta gamma\n");
        try
        {
            Assert.Equal(0, Run(string.Empty, "-w", file));
            Assert.Equal("3 " + file, Stdout().Trim());
        }
        finally
        {
            File.Delete(file);
        }
    }

    [Fact]
    public void AnUnreadableFileIsReportedAndExitsOne()
    {
        string missing = Path.Combine(Path.GetTempPath(), Path.GetRandomFileName());

        Assert.Equal(1, Run(string.Empty, missing));
        Assert.Contains("cannot open", Stderr(), StringComparison.Ordinal);
    }

    [Fact]
    public void ABadFlagPrintsUsageToStderrAndExitsTwo()
    {
        Assert.Equal(2, Run(string.Empty, "--bogus"));
        Assert.Contains("unknown option", Stderr(), StringComparison.Ordinal);
        Assert.Contains("usage:", Stderr(), StringComparison.Ordinal);
        Assert.Equal(string.Empty, Stdout());
    }

    [Fact]
    public void SeveralFilesGetATotalLine()
    {
        string first = Path.Combine(Path.GetTempPath(), Path.GetRandomFileName());
        string second = Path.Combine(Path.GetTempPath(), Path.GetRandomFileName());
        File.WriteAllText(first, "a b\n");
        File.WriteAllText(second, "c\n");
        try
        {
            Assert.Equal(0, Run(string.Empty, "-l", first, second));

            string[] rows = Stdout().Trim().Split('\n');
            Assert.Equal(3, rows.Length);
            Assert.EndsWith("total", rows[2], StringComparison.Ordinal);
        }
        finally
        {
            File.Delete(first);
            File.Delete(second);
        }
    }
}

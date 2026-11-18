using Xunit;

namespace {{ package_name }}.Tests;

public class JsonlTests
{
    const string Sample =
        "{\"level\":\"info\",\"msg\":\"a\"}\n" +
        "{\"level\":\"error\",\"msg\":\"b\"}\n" +
        "{\"level\":\"info\",\"msg\":\"c\"}\n";

    [Fact]
    public void FiltersByWhere()
    {
        var lines = Jsonl.FilterLines(Sample, "level", "info");
        Assert.Equal(2, lines.Count);
        Assert.All(lines, l => Assert.Contains("\"info\"", l));
    }

    [Fact]
    public void CountsGroupsDeterministically()
    {
        var groups = Jsonl.CountGroups(Sample, null, null, "level");
        Assert.Equal(2, groups["info"]);
        Assert.Equal(1, groups["error"]);
        var keys = groups.Keys.ToList();
        Assert.Equal(new[] { "error", "info" }, keys);
    }

    [Fact]
    public void FiltersThenCounts()
    {
        var groups = Jsonl.CountGroups(Sample, "msg", "a", "level");
        // only one info line with msg a
        Assert.Single(groups);
        Assert.Equal(1, groups["info"]);
    }
}

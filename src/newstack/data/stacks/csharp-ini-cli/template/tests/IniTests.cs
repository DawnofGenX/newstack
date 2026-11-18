using Xunit;

namespace {{ package_name }}.Tests;

public class IniTests
{
    [Fact]
    public void ParsesSectionsAndKeys()
    {
        var document = IniDocument.Parse("top = 1\n[server]\nhost = localhost\nport: 8080\n");
        Assert.Equal(new[] { string.Empty, "server" }, document.Sections);
        Assert.True(document.TryGet("server", "host", out string host));
        Assert.Equal("localhost", host);
        Assert.True(document.TryGetPath("server.port", out string port));
        Assert.Equal("8080", port);
        Assert.True(document.TryGetPath("top", out string top));
        Assert.Equal("1", top);
    }

    [Fact]
    public void StripsCommentsButKeepsHashInsideValues()
    {
        var document = IniDocument.Parse("; comment\nurl = http://example.com/#frag  ; trailing\nquoted = \"a ; b\"\n");
        Assert.True(document.TryGetPath("url", out string url));
        Assert.Equal("http://example.com/#frag", url);
        Assert.True(document.TryGetPath("quoted", out string quoted));
        Assert.Equal("a ; b", quoted);
    }

    [Fact]
    public void LastValueWinsAndKeepsItsPosition()
    {
        var document = IniDocument.Parse("[a]\nx = 1\ny = 2\nx = 3\n");
        Assert.Equal(new[] { string.Empty, "a" }, document.Sections);
        Assert.Equal("x = 3\ny = 2", document.ToIni().Split('\n', 2)[1]);
    }

    [Fact]
    public void MergeLetsTheRightHandSideWin()
    {
        var left = IniDocument.Parse("[a]\nx = 1\ny = 2\n");
        var right = IniDocument.Parse("[a]\nx = 9\n[b]\nz = 3\n");
        left.Merge(right);
        Assert.True(left.TryGetPath("a.x", out string x));
        Assert.Equal("9", x);
        Assert.True(left.TryGetPath("b.z", out string z));
        Assert.Equal("3", z);
        Assert.Contains("[b]", left.ToIni());
    }

    [Fact]
    public void RejectsMalformedLines()
    {
        var error = Assert.Throws<IniException>(() => IniDocument.Parse("not a pair\n"));
        Assert.Equal("line 1: expected [section] or key = value, got 'not a pair'", error.Message);
        Assert.Throws<IniException>(() => IniDocument.Parse("[missing\n"));
        Assert.Throws<IniException>(() => IniDocument.Parse("[]\n"));
    }

    [Fact]
    public void PairsFollowDocumentOrder()
    {
        var document = IniDocument.Parse("a = 1\n[s]\nb = 2\n");
        Assert.Equal(new[] { ("", "a", "1"), ("s", "b", "2") }, document.Pairs().ToArray());
    }

    [Fact]
    public void TreeSortsSectionsAndKeys()
    {
        var document = IniDocument.Parse("[z]\nb = 1\n[y]\na = 2\n");
        var tree = document.ToTree();
        Assert.Equal(new[] { "", "y", "z" }, tree.Keys.ToArray());
    }
}

using Xunit;

namespace {{ package_name }}.Tests;

public class SlugTests
{
    [Fact]
    public void BasicSlug()
    {
        Assert.Equal("hello-world", Slugger.Slugify("Hello World!"));
    }

    [Fact]
    public void CollapsesSeparators()
    {
        Assert.Equal("a-b-c", Slugger.Slugify("a!!!b...c"));
    }

    [Fact]
    public void Trims()
    {
        Assert.Equal("hello", Slugger.Slugify("  Hello!!!  "));
    }

    [Fact]
    public void MaxLength()
    {
        Assert.Equal("hello", Slugger.Slugify("hello world", "-", 5));
    }

    [Fact]
    public void CustomSeparator()
    {
        Assert.Equal("hello_world", Slugger.Slugify("Hello World", "_"));
    }
}

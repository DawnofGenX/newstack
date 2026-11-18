using Xunit;

namespace {{ package_name }}.Tests;

public class ReportTests
{
    [Fact]
    public void RendersFixedWidthTable()
    {
        const string csvText = "name,department,amount\nAda,Engineering,100\nBob,Engineering,200\nCarol,Sales,50\n";
        var csv = Csv.Parse(csvText);
        var rows = Report.Build(csv, "department");
        var actual = Report.RenderTable(rows);
        const string expected =
            "Group       Count     Total\n" +
            "----------- -----  --------\n" +
            "Engineering     2    300.00\n" +
            "Sales           1     50.00\n";
        Assert.Equal(expected, actual);
    }

    [Fact]
    public void JsonRoundTrip()
    {
        const string csvText = "name,department,amount\nAda,Engineering,100\n";
        var csv = Csv.Parse(csvText);
        var rows = Report.Build(csv, "department");
        Assert.Single(rows);
        Assert.Equal("Engineering", rows[0].Group);
        Assert.Equal(1, rows[0].Count);
        Assert.Equal(100m, rows[0].Total);
    }
}

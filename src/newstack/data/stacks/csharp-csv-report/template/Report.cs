using System.Globalization;

namespace {{ package_name }};

public static class Csv
{
    public static (string[] Header, List<string[]> Rows) Parse(string text)
    {
        var lines = text.Split(new[] { "\r\n", "\n" }, StringSplitOptions.None);
        var nonEmpty = lines.Where(l => !string.IsNullOrWhiteSpace(l)).ToList();
        if (nonEmpty.Count == 0)
        {
            throw new ArgumentException("missing header");
        }
        var header = Split(nonEmpty[0]);
        var rows = new List<string[]>();
        foreach (var line in nonEmpty.Skip(1))
        {
            var fields = Split(line);
            if (fields.Length != header.Length)
            {
                throw new ArgumentException("bad column count");
            }
            rows.Add(fields);
        }
        return (header, rows);
    }

    private static string[] Split(string line)
    {
        return line.Split(',', StringSplitOptions.TrimEntries);
    }
}

public sealed record GroupRow(string Group, int Count, decimal Total);

public static class Report
{
    public static List<GroupRow> Build((string[] Header, List<string[]> Rows) csv, string groupColumn, string valueColumn = "amount")
    {
        var header = csv.Header;
        var gi = Array.IndexOf(header, groupColumn);
        if (gi < 0) throw new ArgumentException("missing group column");
        var vi = Array.IndexOf(header, valueColumn);
        if (vi < 0) throw new ArgumentException("missing value column");

        var groups = new Dictionary<string, (int Count, decimal Total)>(StringComparer.Ordinal);
        foreach (var row in csv.Rows)
        {
            var key = row[gi];
            var amount = decimal.Parse(row[vi], CultureInfo.InvariantCulture);
            if (!groups.TryGetValue(key, out var agg))
            {
                agg = (0, 0m);
            }
            groups[key] = (agg.Count + 1, agg.Total + amount);
        }
        return groups
            .OrderBy(kv => kv.Key, StringComparer.Ordinal)
            .Select(kv => new GroupRow(kv.Key, kv.Value.Count, kv.Value.Total))
            .ToList();
    }

    public static string RenderTable(List<GroupRow> rows)
    {
        var groupWidth = Math.Max(5, rows.Count == 0 ? 5 : rows.Max(r => r.Group.Length));
        const int countWidth = 5;
        const int totalWidth = 8;
        var sb = new System.Text.StringBuilder();
        sb.AppendLine(string.Format(CultureInfo.InvariantCulture, "{0,-" + groupWidth + "} {1," + countWidth + "}  {2," + totalWidth + "}", "Group", "Count", "Total"));
        sb.AppendLine(new string('-', groupWidth) + " " + new string('-', countWidth) + "  " + new string('-', totalWidth));
        foreach (var r in rows)
        {
            sb.AppendLine(string.Format(CultureInfo.InvariantCulture, "{0,-" + groupWidth + "} {1," + countWidth + "}  {2," + totalWidth + ":F2}", r.Group, r.Count, r.Total));
        }
        return sb.ToString();
    }
}

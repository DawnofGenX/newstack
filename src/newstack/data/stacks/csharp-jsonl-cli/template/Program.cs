// csharp-jsonl-cli

using System.Text.Json;

namespace {{ package_name }};

class Program
{
    static int Main(string[] args)
    {
        string? inputPath = null;
        string? where = null;
        string? group = null;
        bool count = false;
        bool json = false;

        for (int i = 0; i < args.Length; i++)
        {
            switch (args[i])
            {
                case "--where":
                    where = args[++i];
                    break;
                case "--group":
                    group = args[++i];
                    break;
                case "--count":
                    count = true;
                    break;
                case "--json":
                    json = true;
                    break;
                default:
                    inputPath = args[i];
                    break;
            }
        }

        string text = inputPath is null
            ? Console.In.ReadToEnd()
            : File.ReadAllText(inputPath);

        string? whereField = null;
        string? whereValue = null;
        if (where is not null)
        {
            var idx = where.IndexOf('=');
            if (idx < 0) { Console.Error.WriteLine("bad --where"); return 2; }
            whereField = where[..idx];
            whereValue = where[(idx + 1)..];
        }

        if (group is not null && count)
        {
            var groups = Jsonl.CountGroups(text, whereField, whereValue, group);
            if (json)
            {
                var arr = groups.Select(kv => new { group = kv.Key, count = kv.Value });
                Console.WriteLine(JsonSerializer.Serialize(arr));
            }
            else
            {
                foreach (var kv in groups)
                {
                    Console.WriteLine($"{kv.Key} {kv.Value}");
                }
            }
            return 0;
        }

        foreach (var line in Jsonl.FilterLines(text, whereField, whereValue))
        {
            Console.WriteLine(line);
        }
        return 0;
    }
}

public static class Jsonl
{
    public static List<string> FilterLines(string text, string? whereField, string? whereValue)
    {
        var result = new List<string>();
        foreach (var line in NonEmptyLines(text))
        {
            using var doc = JsonDocument.Parse(line);
            if (whereField is not null)
            {
                if (!doc.RootElement.TryGetProperty(whereField, out var prop)) continue;
                if (prop.ToString() != whereValue) continue;
            }
            result.Add(line);
        }
        return result;
    }

    public static Dictionary<string, int> CountGroups(string text, string? whereField, string? whereValue, string groupField)
    {
        var groups = new Dictionary<string, int>(StringComparer.Ordinal);
        foreach (var line in FilterLines(text, whereField, whereValue))
        {
            using var doc = JsonDocument.Parse(line);
            if (!doc.RootElement.TryGetProperty(groupField, out var prop)) continue;
            var key = prop.ToString();
            groups[key] = groups.TryGetValue(key, out var c) ? c + 1 : 1;
        }
        return groups.OrderBy(kv => kv.Key, StringComparer.Ordinal)
            .ToDictionary(kv => kv.Key, kv => kv.Value);
    }

    private static IEnumerable<string> NonEmptyLines(string text)
    {
        return text.Split(new[] { "\r\n", "\n" }, StringSplitOptions.None)
            .Where(l => !string.IsNullOrWhiteSpace(l));
    }
}

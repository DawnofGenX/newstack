namespace {{ package_name }};

/// <summary>Raised for anything the parser cannot make sense of.</summary>
public sealed class IniException : Exception
{
    public IniException(string message) : base(message)
    {
    }
}

/// <summary>A parsed INI file: ordered sections, ordered keys, last value wins.</summary>
public sealed class IniDocument
{
    private readonly List<string> sections = new();
    private readonly Dictionary<string, List<KeyValuePair<string, string>>> keys = new(StringComparer.Ordinal);

    public IReadOnlyList<string> Sections => sections;

    public static IniDocument Parse(string text)
    {
        var document = new IniDocument();
        string current = string.Empty;
        document.SectionsOf(current);
        string[] lines = text.Replace("\r\n", "\n").Replace('\r', '\n').Split('\n');
        for (int index = 0; index < lines.Length; index++)
        {
            string line = StripComment(lines[index]).Trim();
            if (line.Length == 0)
            {
                continue;
            }
            if (line.StartsWith('['))
            {
                if (!line.EndsWith(']'))
                {
                    throw new IniException($"line {index + 1}: unterminated section header: '{line}'");
                }
                string name = line[1..^1].Trim();
                if (name.Length == 0)
                {
                    throw new IniException($"line {index + 1}: empty section name");
                }
                document.SectionsOf(name);
                current = name;
                continue;
            }
            int separator = line.IndexOfAny(new[] { '=', ':' });
            if (separator <= 0)
            {
                throw new IniException($"line {index + 1}: expected [section] or key = value, got '{line}'");
            }
            string key = line[..separator].Trim();
            string value = Unquote(line[(separator + 1)..].Trim());
            if (key.Length == 0)
            {
                throw new IniException($"line {index + 1}: empty key");
            }
            document.Set(current, key, value);
        }
        return document;
    }

    private List<KeyValuePair<string, string>> SectionsOf(string section)
    {
        if (!keys.TryGetValue(section, out var list))
        {
            list = new List<KeyValuePair<string, string>>();
            keys[section] = list;
            sections.Add(section);
        }
        return list;
    }

    public bool HasSection(string section) => keys.ContainsKey(section);

    public bool TryGet(string section, string key, out string value)
    {
        value = string.Empty;
        if (!keys.TryGetValue(section, out var list))
        {
            return false;
        }
        foreach (var pair in list)
        {
            if (pair.Key == key)
            {
                value = pair.Value;
                return true;
            }
        }
        return false;
    }

    /// <summary>Look up "section.key"; a bare key means the unnamed section.</summary>
    public bool TryGetPath(string path, out string value)
    {
        int dot = path.LastIndexOf('.');
        return dot < 0 ? TryGet(string.Empty, path, out value) : TryGet(path[..dot], path[(dot + 1)..], out value);
    }

    public void Set(string section, string key, string value)
    {
        var list = SectionsOf(section);
        for (int index = 0; index < list.Count; index++)
        {
            if (list[index].Key == key)
            {
                list[index] = new KeyValuePair<string, string>(key, value);
                return;
            }
        }
        list.Add(new KeyValuePair<string, string>(key, value));
    }

    /// <summary>Values from <paramref name="other"/> win; sections and keys are appended in order.</summary>
    public void Merge(IniDocument other)
    {
        foreach (string section in other.sections)
        {
            foreach (var pair in other.keys[section])
            {
                Set(section, pair.Key, pair.Value);
            }
        }
    }

    public IEnumerable<(string Section, string Key, string Value)> Pairs()
    {
        foreach (string section in sections)
        {
            foreach (var pair in keys[section])
            {
                yield return (section, pair.Key, pair.Value);
            }
        }
    }

    public string ToIni()
    {
        var builder = new System.Text.StringBuilder();
        foreach (string section in sections)
        {
            if (section.Length > 0)
            {
                if (builder.Length > 0)
                {
                    builder.Append('\n');
                }
                builder.Append('[').Append(section).Append(']').Append('\n');
            }
            foreach (var pair in keys[section])
            {
                builder.Append(pair.Key).Append(" = ").Append(pair.Value).Append('\n');
            }
        }
        return builder.ToString().TrimEnd('\n');
    }

    public SortedDictionary<string, SortedDictionary<string, string>> ToTree()
    {
        var tree = new SortedDictionary<string, SortedDictionary<string, string>>(StringComparer.Ordinal);
        foreach (string section in sections)
        {
            var bucket = new SortedDictionary<string, string>(StringComparer.Ordinal);
            foreach (var pair in keys[section])
            {
                bucket[pair.Key] = pair.Value;
            }
            tree[section] = bucket;
        }
        return tree;
    }

    private static string StripComment(string line)
    {
        bool quoted = false;
        for (int index = 0; index < line.Length; index++)
        {
            char character = line[index];
            if (character == '"')
            {
                quoted = !quoted;
            }
            else if (!quoted && (character == ';' || character == '#') && (index == 0 || char.IsWhiteSpace(line[index - 1])))
            {
                return line[..index];
            }
        }
        return line;
    }

    private static string Unquote(string value)
    {
        if (value.Length >= 2 && value[0] == '"' && value[^1] == '"')
        {
            return value[1..^1].Replace("\\n", "\n").Replace("\\t", "\t");
        }
        return value;
    }
}

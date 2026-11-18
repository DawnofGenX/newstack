namespace {{ package_name }};

using System.Text.Json;

/// <summary>The command line front end, public so tests can call it directly.</summary>
public static class Ini
{
    private const string Usage = """
        Usage: {{ npm_name }} [options] [file...]

        Options:
          --json            print the whole document as JSON (the default)
          --get PATH        print one value: section.key, or key for the unnamed section
          --section NAME    restrict --json to one section
          --list-sections   print the section names, one per line
          --ini             print the merged document back as INI
          -h, --help        show this message

        Several files are merged left to right, later values winning. Without a
        file the document is read from stdin. Unknown options exit 2, unreadable
        files and malformed documents exit 1.
        """;

    private static readonly JsonSerializerOptions Options = new() { WriteIndented = true };

    public static int Run(string[] args)
    {
        var files = new List<string>();
        string? get = null;
        string? section = null;
        string format = "json";
        for (int index = 0; index < args.Length; index++)
        {
            switch (args[index])
            {
                case "-h":
                case "--help":
                    Console.WriteLine(Usage);
                    return 0;
                case "--json":
                    format = "json";
                    break;
                case "--ini":
                    format = "ini";
                    break;
                case "--get":
                    if (++index >= args.Length)
                    {
                        return UsageError("--get needs a path");
                    }
                    get = args[index];
                    break;
                case "--section":
                    if (++index >= args.Length)
                    {
                        return UsageError("--section needs a name");
                    }
                    section = args[index];
                    break;
                case "--list-sections":
                    format = "sections";
                    break;
                default:
                    if (args[index].StartsWith('-') && args[index] != "-")
                    {
                        return UsageError($"unknown option {args[index]}");
                    }
                    files.Add(args[index]);
                    break;
            }
        }

        IniDocument document;
        try
        {
            if (files.Count == 0)
            {
                document = IniDocument.Parse(Console.In.ReadToEnd());
            }
            else
            {
                document = IniDocument.Parse(File.ReadAllText(files[0]));
                for (int index = 1; index < files.Count; index++)
                {
                    document.Merge(IniDocument.Parse(File.ReadAllText(files[index])));
                }
            }
        }
        catch (Exception error) when (error is IOException or IniException)
        {
            Console.Error.WriteLine($"{{ npm_name }}: {error.Message}");
            return 1;
        }

        if (get is not null)
        {
            if (!document.TryGetPath(get, out string value))
            {
                Console.Error.WriteLine($"{{ npm_name }}: no such key: {get}");
                return 1;
            }
            Console.WriteLine(value);
            return 0;
        }

        switch (format)
        {
            case "ini":
                Console.WriteLine(document.ToIni());
                return 0;
            case "sections":
                foreach (string name in document.Sections)
                {
                    Console.WriteLine(name.Length == 0 ? "(default)" : name);
                }
                return 0;
            default:
                var tree = document.ToTree();
                if (section is not null)
                {
                    if (!tree.TryGetValue(section, out var only))
                    {
                        Console.Error.WriteLine($"{{ npm_name }}: no such section: {section}");
                        return 1;
                    }
                    Console.WriteLine(JsonSerializer.Serialize(only, Options));
                    return 0;
                }
                Console.WriteLine(JsonSerializer.Serialize(tree, Options));
                return 0;
        }
    }

    private static int UsageError(string message)
    {
        Console.Error.WriteLine($"{{ npm_name }}: {message}");
        Console.Error.WriteLine(Usage);
        return 2;
    }
}

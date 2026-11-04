namespace {{ package_name }};

/// <summary>How argument parsing ended.</summary>
public enum Status
{
    Ok,
    Help,
    Version,
    Error,
}

/// <summary>
/// Parsed command line: which figures to print, the files, and how parsing ended.
/// With no flag all three figures are printed (like <c>wc</c> with no flags);
/// with any flag only the selected ones are.
/// </summary>
public sealed class Options
{
    public const string Version = "0.1.0";

    private Options(bool lines, bool words, bool bytes, IReadOnlyList<string> files, Status status, string error)
    {
        Lines = lines;
        Words = words;
        Bytes = bytes;
        Files = files;
        Status = status;
        Error = error;
    }

    public bool Lines { get; }
    public bool Words { get; }
    public bool Bytes { get; }

    public IReadOnlyList<string> Files { get; }
    public Status Status { get; }
    public string Error { get; }

    /// <summary>Hand-rolled parser: no dependency, and every branch is unit tested.</summary>
    public static Options Parse(IReadOnlyList<string> args)
    {
        bool? lines = null, words = null, bytes = null;
        bool anyFlag = false;
        bool onlyFiles = false;
        var files = new List<string>();

        foreach (string arg in args)
        {
            if (onlyFiles || arg.Length == 0 || arg == "-")
            {
                files.Add(arg);
                continue;
            }

            if (arg == "--")
            {
                onlyFiles = true;
                continue;
            }

            if (arg is "-h" or "--help")
            {
                return Finish(lines, words, bytes, anyFlag, files, Status.Help, string.Empty);
            }

            if (arg is "-V" or "--version")
            {
                return Finish(lines, words, bytes, anyFlag, files, Status.Version, string.Empty);
            }

            if (arg is "-l" or "--lines") { lines = true; anyFlag = true; continue; }
            if (arg is "-w" or "--words") { words = true; anyFlag = true; continue; }
            if (arg is "-c" or "--bytes") { bytes = true; anyFlag = true; continue; }

            if (arg.StartsWith('-'))
            {
                return Finish(lines, words, bytes, anyFlag, files, Status.Error, $"unknown option '{arg}'");
            }

            files.Add(arg);
        }

        return Finish(lines, words, bytes, anyFlag, files, Status.Ok, string.Empty);
    }

    private static Options Finish(
        bool? lines, bool? words, bool? bytes, bool anyFlag,
        IReadOnlyList<string> files, Status status, string error)
    {
        // No flag at all: print all three figures (like wc with no flags).
        // Any flag: print only the selected figures.
        bool l = anyFlag ? lines ?? false : true;
        bool w = anyFlag ? words ?? false : true;
        bool b = anyFlag ? bytes ?? false : true;
        return new Options(l, w, b, files, status, error);
    }

    /// <summary>Help text; the program name comes from the assembly so it matches the binary.</summary>
    public static string Usage(string program) =>
        $"usage: {program} [-l] [-w] [-c] [--] [FILE ...]\n"
        + "\n"
        + "Count lines, words and bytes in each FILE, or in standard input\n"
        + "when no FILE is given. With more than one FILE a total is printed.\n"
        + "With no flag all three figures are printed; with any flag only the\n"
        + "selected ones are.\n"
        + "\n"
        + "  -l, --lines     print the line count\n"
        + "  -w, --words     print the word count\n"
        + "  -c, --bytes     print the byte count\n"
        + "  -h, --help      show this help and exit\n"
        + "  -V, --version   show the version and exit\n";
}

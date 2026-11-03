namespace {{ package_name }};

/// <summary>Which figures to print; <see cref="Mode.All"/> prints lines, words and bytes.</summary>
public enum Mode
{
    All,
    Lines,
    Words,
    Bytes,
}

/// <summary>How argument parsing ended.</summary>
public enum Status
{
    Ok,
    Help,
    Version,
    Error,
}

/// <summary>Parsed command line: the chosen mode, the files, and how parsing ended.</summary>
public sealed class Options
{
    public const string Version = "0.1.0";

    private Options(Mode mode, IReadOnlyList<string> files, Status status, string error)
    {
        Mode = mode;
        Files = files;
        Status = status;
        Error = error;
    }

    public Mode Mode { get; }

    public IReadOnlyList<string> Files { get; }

    public Status Status { get; }

    public string Error { get; }

    /// <summary>Hand-rolled parser: no dependency, and every branch is unit tested.</summary>
    public static Options Parse(IReadOnlyList<string> args)
    {
        Mode? chosen = null;
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
                return new Options(chosen ?? Mode.All, files, Status.Help, string.Empty);
            }

            if (arg is "-V" or "--version")
            {
                return new Options(chosen ?? Mode.All, files, Status.Version, string.Empty);
            }

            Mode? requested = ModeFor(arg);
            if (requested is not null)
            {
                if (chosen is not null && chosen != requested)
                {
                    return new Options(
                        chosen.Value,
                        files,
                        Status.Error,
                        $"choose one of -l, -w, -c: '{arg}' conflicts with an earlier mode");
                }

                chosen = requested;
                continue;
            }

            if (arg.StartsWith('-'))
            {
                return new Options(
                    chosen ?? Mode.All,
                    files,
                    Status.Error,
                    $"unknown option '{arg}'");
            }

            files.Add(arg);
        }

        return new Options(chosen ?? Mode.All, files, Status.Ok, string.Empty);
    }

    private static Mode? ModeFor(string arg) => arg switch
    {
        "-l" or "--lines" => Mode.Lines,
        "-w" or "--words" => Mode.Words,
        "-c" or "--bytes" => Mode.Bytes,
        _ => null,
    };

    /// <summary>Help text; the program name comes from the assembly so it matches the binary.</summary>
    public static string Usage(string program) =>
        $"usage: {program} [-l | -w | -c] [--] [FILE ...]\n"
        + "\n"
        + "Count lines, words and bytes in each FILE, or in standard input\n"
        + "when no FILE is given. With more than one FILE a total is printed.\n"
        + "\n"
        + "  -l, --lines     print the line count only\n"
        + "  -w, --words     print the word count only\n"
        + "  -c, --bytes     print the byte count only\n"
        + "  -h, --help      show this help and exit\n"
        + "  -V, --version   show the version and exit\n";
}

using System.Globalization;

namespace {{ package_name }};

/// <summary>
/// The runnable command: turns argv into output and an exit code.
/// <para>
/// Nothing here calls <c>Environment.Exit</c>, so tests drive <see cref="Run"/> directly.
/// Exit codes: <c>0</c> success, <c>1</c> unreadable input, <c>2</c> bad usage.
/// </para>
/// </summary>
public sealed class Cli
{
    private readonly TextReader _stdin;
    private readonly string _program;

    public Cli(TextReader stdin, string program)
    {
        _stdin = stdin;
        _program = program;
    }

    public int Run(IReadOnlyList<string> args, TextWriter output, TextWriter error)
    {
        Options options = Options.Parse(args);
        switch (options.Status)
        {
            case Status.Help:
                output.Write(Options.Usage(_program));
                return 0;
            case Status.Version:
                output.WriteLine(Options.Version);
                return 0;
            case Status.Error:
                error.WriteLine("error: " + options.Error);
                error.WriteLine();
                error.Write(Options.Usage(_program));
                return 2;
        }

        if (options.Files.Count == 0)
        {
            string? piped = ReadStandardInput();
            if (piped is null)
            {
                error.WriteLine("error: cannot read standard input");
                return 1;
            }

            Print(output, TextStat.Count(piped), options, string.Empty);
            return 0;
        }

        var total = new Counts(0, 0, 0);
        bool failed = false;
        foreach (string path in options.Files)
        {
            Counts counts;
            if (path == "-")
            {
                string? piped = ReadStandardInput();
                if (piped is null)
                {
                    error.WriteLine("error: cannot read standard input");
                    failed = true;
                    continue;
                }

                counts = TextStat.Count(piped);
                Print(output, counts, options, string.Empty);
            }
            else
            {
                try
                {
                    counts = TextStat.Count(System.IO.File.ReadAllBytes(path));
                }
                catch (Exception exc) when (exc is IOException or UnauthorizedAccessException)
                {
                    error.WriteLine($"error: cannot open '{path}'");
                    failed = true;
                    continue;
                }

                Print(output, counts, options, path);
            }

            total = total.Plus(counts);
        }

        if (options.Files.Count > 1)
        {
            Print(output, total, options, "total");
        }

        return failed ? 1 : 0;
    }

    private string? ReadStandardInput()
    {
        try
        {
            return _stdin.ReadToEnd();
        }
        catch (IOException)
        {
            return null;
        }
    }

    private static void Print(TextWriter output, Counts counts, Options options, string label)
    {
        var line = new System.Text.StringBuilder();
        if (options.Lines)
        {
            line.Append(Format(counts.Lines));
        }

        if (options.Words)
        {
            line.Append(Format(counts.Words));
        }

        if (options.Bytes)
        {
            line.Append(Format(counts.Bytes));
        }

        if (label.Length > 0)
        {
            line.Append(' ').Append(label);
        }

        output.WriteLine(line.ToString());
    }

    private static string Format(long value) =>
        string.Format(CultureInfo.InvariantCulture, "{0,8}", value);
}

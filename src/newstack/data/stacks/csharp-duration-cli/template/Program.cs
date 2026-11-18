// csharp-duration-cli — parse, format and add ISO 8601 durations.
using System.Globalization;

return Durations.Run(args);

public static class Durations
{
    private const string Usage = """
        Usage: dotnet run -- COMMAND [options]

        Work with ISO 8601 durations (P1W, P2DT3H4M5S, PT45S) and their terse
        human spelling (1h30m, 2d, -45s).

        Commands:
          parse VALUE             print the duration as seconds, ISO and human
          add VALUE --from WHEN   print WHEN plus VALUE (WHEN defaults to now, UTC)
          between FROM TO         print TO - FROM as a duration
        Options:
          -h, --help              show this help and exit

        Exit codes:
          0  success
          1  a value could not be parsed
          2  usage error
        """;

    public static int Run(string[] argv)
    {
        if (argv.Length == 0)
        {
            return UsageError("a command is required");
        }

        if (argv[0] is "-h" or "--help")
        {
            Console.Out.WriteLine(Usage);
            return 0;
        }

        var command = argv[0];
        var rest = argv.Skip(1).ToArray();

        try
        {
            return command switch
            {
                "parse" => Parse(rest),
                "add" => Add(rest),
                "between" => Between(rest),
                _ => UsageError($"unknown command: {command}"),
            };
        }
        catch (FormatException error)
        {
            Console.Error.WriteLine($"csharp-duration-cli: {error.Message}");
            return 1;
        }
    }

    private static int Parse(string[] rest)
    {
        if (rest.Length != 1)
        {
            return UsageError("parse takes exactly one value");
        }

        var duration = IsoDuration.Parse(rest[0]);
        Console.Out.WriteLine($"seconds={duration.TotalSeconds.ToString("0.###", CultureInfo.InvariantCulture)}");
        Console.Out.WriteLine($"iso={duration.ToIso()}");
        Console.Out.WriteLine($"human={duration.ToHuman()}");
        return 0;
    }

    private static int Add(string[] rest)
    {
        if (rest.Length == 0)
        {
            return UsageError("add needs a duration");
        }

        var duration = IsoDuration.Parse(rest[0]);
        var from = DateTimeOffset.UtcNow;
        for (var index = 1; index < rest.Length; index++)
        {
            switch (rest[index])
            {
                case "--from" when index + 1 < rest.Length:
                    from = ReadInstant(rest[++index]);
                    break;
                case "--from":
                    return UsageError("--from needs a timestamp");
                default:
                    return UsageError($"unknown argument: {rest[index]}");
            }
        }

        var result = duration.AddTo(from);
        Console.Out.WriteLine($"from={from.UtcDateTime.ToString("yyyy-MM-ddTHH:mm:ssZ", CultureInfo.InvariantCulture)}");
        Console.Out.WriteLine($"to={result.UtcDateTime.ToString("yyyy-MM-ddTHH:mm:ssZ", CultureInfo.InvariantCulture)}");
        return 0;
    }

    private static int Between(string[] rest)
    {
        if (rest.Length != 2)
        {
            return UsageError("between takes exactly two timestamps");
        }

        var from = ReadInstant(rest[0]);
        var to = ReadInstant(rest[1]);
        var difference = new IsoDuration(to - from);
        Console.Out.WriteLine($"seconds={difference.TotalSeconds.ToString("0.###", CultureInfo.InvariantCulture)}");
        Console.Out.WriteLine($"iso={difference.ToIso()}");
        Console.Out.WriteLine($"human={difference.ToHuman()}");
        return 0;
    }

    private static DateTimeOffset ReadInstant(string text)
    {
        if (DateTimeOffset.TryParse(
                text,
                CultureInfo.InvariantCulture,
                DateTimeStyles.AssumeUniversal | DateTimeStyles.AdjustToUniversal,
                out var parsed) is false)
        {
            throw new FormatException($"not a timestamp (try 2026-01-01T00:00:00Z): {text}");
        }

        return parsed;
    }

    private static int UsageError(string message)
    {
        Console.Error.WriteLine($"csharp-duration-cli: {message}");
        Console.Error.WriteLine(Usage);
        return 2;
    }
}

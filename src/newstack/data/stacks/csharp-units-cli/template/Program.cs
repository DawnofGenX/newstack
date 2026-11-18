// csharp-units-cli

using System.Globalization;

namespace {{ package_name }};

internal static class Program
{
    private const string Usage =
        "usage: {{ npm_name }} convert VALUE FROM TO\n" +
        "       {{ npm_name }} list\n" +
        "       {{ npm_name }} units DIMENSION";

    private static int Main(string[] args)
    {
        try
        {
            if (args.Length == 0)
            {
                Console.Error.WriteLine(Usage);
                return 2;
            }

            return args[0].ToLowerInvariant() switch
            {
                "convert" => Convert(args),
                "list" => List(),
                "units" => UnitsForDimension(args),
                "-h" or "--help" or "help" => Help(),
                _ => Fail($"unknown command: {args[0]}"),
            };
        }
        catch (ArgumentException error)
        {
            Console.Error.WriteLine($"error: {error.Message}");
            return 1;
        }
    }

    private static int Convert(string[] args)
    {
        if (args.Length != 4)
        {
            return Fail("convert needs exactly VALUE FROM TO");
        }
        if (!double.TryParse(args[1], NumberStyles.Float, CultureInfo.InvariantCulture, out double value))
        {
            return Fail($"not a number: {args[1]}");
        }
        double converted = Units.Convert(value, args[2], args[3]);
        Console.WriteLine($"{Units.Format(converted)} {args[3]}");
        return 0;
    }

    private static int List()
    {
        foreach (var dimension in Units.Dimensions)
        {
            Console.WriteLine($"{dimension.ToString().ToLowerInvariant()}: {string.Join(' ', Units.Symbols(dimension))}");
        }
        return 0;
    }

    private static int UnitsForDimension(string[] args)
    {
        if (args.Length != 2)
        {
            return Fail("units needs a dimension name");
        }
        if (!Enum.TryParse<Dimension>(args[1], ignoreCase: true, out var dimension))
        {
            return Fail($"unknown dimension: {args[1]}");
        }
        Console.WriteLine(string.Join(' ', Units.Symbols(dimension)));
        return 0;
    }

    private static int Help()
    {
        Console.WriteLine(Usage);
        return 0;
    }

    private static int Fail(string message)
    {
        Console.Error.WriteLine($"error: {message}");
        Console.Error.WriteLine(Usage);
        return 2;
    }
}

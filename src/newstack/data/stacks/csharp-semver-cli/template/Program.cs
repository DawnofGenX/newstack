// csharp-semver-cli
//
// Commands:
//   parse VERSION              print the components
//   compare LEFT RIGHT         print -1, 0 or 1
//   bump patch|minor|major V   print the next version
//   satisfies VERSION RANGE    exit 0 and print true, or exit 1 and print false
using {{ package_name }};

return Semver.Run(args);

/// <summary>argv handling; kept separate from <see cref="SemVersion"/> so tests can call it.</summary>
public static class Semver
{
    public static int Run(string[] args)
    {
        if (args.Length == 0 || args[0] is "--help" or "-h")
        {
            Console.Out.Write(Usage);
            return args.Length == 0 ? 2 : 0;
        }

        try
        {
            return args[0] switch
            {
                "parse" => Parse(args),
                "compare" => Compare(args),
                "bump" => Bump(args),
                "satisfies" => Satisfies(args),
                _ => Fail($"unknown command \"{args[0]}\"", 2),
            };
        }
        catch (FormatException error)
        {
            return Fail(error.Message, 1);
        }
        catch (ArgumentException error)
        {
            return Fail(error.Message, 2);
        }
    }

    private const string Usage = """
        csharp-semver-cli — read and compare semantic versions

        Usage:
          csharp-semver-cli parse VERSION
          csharp-semver-cli compare LEFT RIGHT
          csharp-semver-cli bump patch|minor|major VERSION
          csharp-semver-cli satisfies VERSION RANGE

        Exit codes: 0 matched/ok, 1 did not match or invalid version, 2 usage.
        """;

    private static int Parse(string[] args)
    {
        if (args.Length != 2)
        {
            return Fail("parse needs one version", 2);
        }

        if (!SemVersion.TryParse(args[1], out var version))
        {
            return Fail($"invalid version \"{args[1]}\"", 1);
        }

        Console.Out.WriteLine($"major={version.Major} minor={version.Minor} patch={version.Patch}");
        if (version.IsPrerelease)
        {
            Console.Out.WriteLine($"prerelease={version.Prerelease}");
        }

        if (version.Build.Length > 0)
        {
            Console.Out.WriteLine($"build={version.Build}");
        }

        return 0;
    }

    private static int Compare(string[] args)
    {
        if (args.Length != 3)
        {
            return Fail("compare needs two versions", 2);
        }

        var left = SemVersion.Parse(args[1]);
        var right = SemVersion.Parse(args[2]);
        Console.Out.WriteLine(left.CompareTo(right).ToString());
        return 0;
    }

    private static int Bump(string[] args)
    {
        if (args.Length != 3)
        {
            return Fail("bump needs a part and a version", 2);
        }

        var version = SemVersion.Parse(args[2]);
        var next = args[1] switch
        {
            "major" => new SemVersion(version.Major + 1, 0, 0),
            "minor" => new SemVersion(version.Major, version.Minor + 1, 0),
            "patch" => new SemVersion(version.Major, version.Minor, version.Patch + 1),
            _ => throw new ArgumentException($"unknown part \"{args[1]}\"", nameof(args)),
        };
        Console.Out.WriteLine(next.ToString());
        return 0;
    }

    private static int Satisfies(string[] args)
    {
        if (args.Length != 3)
        {
            return Fail("satisfies needs a version and a range", 2);
        }

        var version = SemVersion.Parse(args[1]);
        var matched = Ranges.Satisfies(version, args[2]);
        Console.Out.WriteLine(matched ? "true" : "false");
        return matched ? 0 : 1;
    }

    private static int Fail(string message, int status)
    {
        Console.Error.WriteLine($"csharp-semver-cli: {message}");
        return status;
    }
}

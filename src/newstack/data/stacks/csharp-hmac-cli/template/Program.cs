// csharp-hmac-cli
//
// Commands:
//   sign   --key K --message M [--algo sha256]
//   verify --key K --message M --digest HEX [--algo sha256]
//   sign-file --key K FILE [--algo sha256]
using System.Text;
using {{ package_name }};

return HmacCli.Run(args);

/// <summary>argv handling for the HMAC tool.</summary>
public static class HmacCli
{
    private const string Usage = """
        csharp-hmac-cli — sign and verify messages with HMAC

        Usage:
          csharp-hmac-cli sign      --key KEY --message TEXT [--algo ALGO]
          csharp-hmac-cli sign-file --key KEY FILE [--algo ALGO]
          csharp-hmac-cli verify    --key KEY --message TEXT --digest HEX [--algo ALGO]

        ALGO is one of sha256 (default), sha384, sha512, sha1 or md5.

        Exit codes: 0 ok/matched, 1 did not match or unreadable file, 2 usage.
        """;

    public static int Run(string[] args)
    {
        if (args.Length == 0)
        {
            Console.Error.Write(Usage);
            return 2;
        }

        if (args[0] is "-h" or "--help")
        {
            Console.Out.Write(Usage);
            return 0;
        }

        var options = new Dictionary<string, string>(StringComparer.Ordinal);
        var positional = new List<string>();
        for (var i = 1; i < args.Length; i += 1)
        {
            var argument = args[i];
            if (!argument.StartsWith("--", StringComparison.Ordinal))
            {
                positional.Add(argument);
                continue;
            }

            var value = i + 1 < args.Length && !args[i + 1].StartsWith("--", StringComparison.Ordinal) ? args[i + 1] : null;
            if (value is null)
            {
                return Fail($"{argument} needs a value", 2);
            }

            options[argument.TrimStart('-')] = value;
            i += 1;
        }

        var algorithm = options.TryGetValue("algo", out var requested) ? requested : "sha256";
        if (!Hmac.Algorithms.Contains(algorithm, StringComparer.OrdinalIgnoreCase))
        {
            return Fail($"unsupported algorithm \"{algorithm}\"", 2);
        }

        if (!options.TryGetValue("key", out var key) || key.Length == 0)
        {
            return Fail("--key is required", 2);
        }

        try
        {
            return args[0] switch
            {
                "sign" => Sign(key, options, algorithm),
                "verify" => Verify(key, options, algorithm),
                "sign-file" => SignFile(key, options, positional, algorithm),
                _ => Fail($"unknown command \"{args[0]}\"", 2),
            };
        }
        catch (IOException error)
        {
            return Fail(error.Message, 1);
        }
    }

    private static int Sign(string key, Dictionary<string, string> options, string algorithm)
    {
        if (!options.TryGetValue("message", out var message))
        {
            return Fail("--message is required", 2);
        }

        Console.Out.WriteLine(Hmac.SignHex(algorithm, key, message));
        return 0;
    }

    private static int SignFile(string key, Dictionary<string, string> options, List<string> positional, string algorithm)
    {
        if (positional.Count != 1)
        {
            return Fail("sign-file needs exactly one path", 2);
        }

        var path = positional[0];
        if (!File.Exists(path))
        {
            return Fail($"cannot read {path}", 1);
        }

        var bytes = File.ReadAllBytes(path);
        var digest = Convert.ToHexString(Hmac.Sign(algorithm, Encoding.UTF8.GetBytes(key), bytes)).ToLowerInvariant();
        Console.Out.WriteLine($"{digest}  {path}");
        return 0;
    }

    private static int Verify(string key, Dictionary<string, string> options, string algorithm)
    {
        if (!options.TryGetValue("message", out var message))
        {
            return Fail("--message is required", 2);
        }

        if (!options.TryGetValue("digest", out var digest))
        {
            return Fail("--digest is required", 2);
        }

        var matched = Hmac.Verify(algorithm, Encoding.UTF8.GetBytes(key), Encoding.UTF8.GetBytes(message), digest);
        Console.Out.WriteLine(matched ? "match" : "mismatch");
        return matched ? 0 : 1;
    }

    private static int Fail(string message, int status)
    {
        Console.Error.WriteLine($"csharp-hmac-cli: {message}");
        return status;
    }
}

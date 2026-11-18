// csharp-jwt-cli

using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

namespace {{ package_name }};

class Program
{
    static int Main(string[] args)
    {
        if (args.Length == 0)
        {
            Console.Error.WriteLine("usage: jwt encode|decode|verify ...");
            return 2;
        }

        switch (args[0])
        {
            case "encode":
                return Encode(args[1..]);
            case "decode":
                return Decode(args[1..]);
            case "verify":
                return Verify(args[1..]);
            default:
                Console.Error.WriteLine("unknown command: " + args[0]);
                return 2;
        }
    }

    static int Encode(string[] args)
    {
        string secret = "secret";
        var claims = new Dictionary<string, string>(StringComparer.Ordinal);
        for (int i = 0; i < args.Length; i++)
        {
            if (args[i] == "--secret")
            {
                secret = args[++i];
            }
            else if (args[i] == "--exp")
            {
                long now = DateTimeOffset.UtcNow.ToUnixTimeSeconds();
                claims["exp"] = (now + long.Parse(args[++i])).ToString();
            }
            else
            {
                int eq = args[i].IndexOf('=');
                if (eq < 0) { Console.Error.WriteLine("bad claim: " + args[i]); return 2; }
                claims[args[i][..eq]] = args[i][(eq + 1)..];
            }
        }
        if (!claims.ContainsKey("sub"))
        {
            claims["sub"] = "anonymous";
        }
        Console.WriteLine(Jwt.Encode(claims, secret));
        return 0;
    }

    static int Decode(string[] args)
    {
        if (args.Length == 0) { Console.Error.WriteLine("usage: jwt decode <token>"); return 2; }
        var (header, payload) = Jwt.Decode(args[0]);
        Console.WriteLine("header=" + header);
        Console.WriteLine("payload=" + payload);
        return 0;
    }

    static int Verify(string[] args)
    {
        string? token = null;
        string secret = "secret";
        for (int i = 0; i < args.Length; i++)
        {
            if (args[i] == "--secret") secret = args[++i];
            else token = args[i];
        }
        if (token is null) { Console.Error.WriteLine("usage: jwt verify <token> --secret <s>"); return 2; }
        bool ok = Jwt.Verify(token, secret);
        Console.WriteLine(ok ? "valid" : "invalid");
        return ok ? 0 : 1;
    }
}

public static class Jwt
{
    public static string Encode(Dictionary<string, string> claims, string secret)
    {
        string headerJson = JsonSerializer.Serialize(new { alg = "HS256", typ = "JWT" });
        string payloadJson = JsonSerializer.Serialize(claims);
        string h = Base64UrlEncode(Encoding.UTF8.GetBytes(headerJson));
        string p = Base64UrlEncode(Encoding.UTF8.GetBytes(payloadJson));
        string sig = Base64UrlEncode(HmacSha256(secret, h + "." + p));
        return h + "." + p + "." + sig;
    }

    public static (string header, string payload) Decode(string token)
    {
        var parts = token.Split('.');
        if (parts.Length != 3) throw new FormatException("bad token");
        string header = Encoding.UTF8.GetString(Base64UrlDecode(parts[0]));
        string payload = Encoding.UTF8.GetString(Base64UrlDecode(parts[1]));
        return (header, payload);
    }

    public static bool Verify(string token, string secret)
    {
        try
        {
            var parts = token.Split('.');
            if (parts.Length != 3) return false;
            byte[] expected = HmacSha256(secret, parts[0] + "." + parts[1]);
            byte[] actual = Base64UrlDecode(parts[2]);
            if (!CryptographicOperations.FixedTimeEquals(expected, actual)) return false;
            // exp check
            string payload = Encoding.UTF8.GetString(Base64UrlDecode(parts[1]));
            using var doc = JsonDocument.Parse(payload);
            if (doc.RootElement.TryGetProperty("exp", out var exp))
            {
                long now = DateTimeOffset.UtcNow.ToUnixTimeSeconds();
                if (now > exp.GetInt64()) return false;
            }
            return true;
        }
        catch
        {
            return false;
        }
    }

    private static byte[] HmacSha256(string secret, string data)
    {
        using var hmac = new HMACSHA256(Encoding.UTF8.GetBytes(secret));
        return hmac.ComputeHash(Encoding.UTF8.GetBytes(data));
    }

    private static string Base64UrlEncode(byte[] data)
    {
        return Convert.ToBase64String(data).TrimEnd('=').Replace('+', '-').Replace('/', '_');
    }

    private static byte[] Base64UrlDecode(string s)
    {
        string pad = s.Replace('-', '+').Replace('_', '/');
        switch (pad.Length % 4)
        {
            case 2: pad += "=="; break;
            case 3: pad += "="; break;
        }
        return Convert.FromBase64String(pad);
    }
}
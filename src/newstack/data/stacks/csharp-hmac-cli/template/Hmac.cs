using System.Security.Cryptography;
using System.Text;

namespace {{ package_name }};

/// <summary>HMAC signing and constant-time verification over UTF-8 or raw bytes.</summary>
public static class Hmac
{
    /// <summary>Algorithm names accepted on the command line.</summary>
    public static readonly string[] Algorithms = ["sha256", "sha384", "sha512", "sha1", "md5"];

    public static byte[] Sign(string algorithm, byte[] key, byte[] message)
    {
        using var mac = Create(algorithm, key);
        return mac.ComputeHash(message);
    }

    public static string SignHex(string algorithm, string key, string message)
    {
        return Convert.ToHexString(Sign(algorithm, Encoding.UTF8.GetBytes(key), Encoding.UTF8.GetBytes(message)))
            .ToLowerInvariant();
    }

    /// <summary>
    /// Compares in constant time, so a caller cannot learn the prefix of the
    /// expected signature from how long verification took.
    /// </summary>
    public static bool Verify(string algorithm, byte[] key, byte[] message, string expectedHex)
    {
        byte[] expected;
        try
        {
            expected = Convert.FromHexString(expectedHex.Trim());
        }
        catch (FormatException)
        {
            return false;
        }

        var actual = Sign(algorithm, key, message);
        return CryptographicOperations.FixedTimeEquals(actual, expected);
    }

    private static HMAC Create(string algorithm, byte[] key)
    {
        return algorithm.ToLowerInvariant() switch
        {
            "sha256" => new HMACSHA256(key),
            "sha384" => new HMACSHA384(key),
            "sha512" => new HMACSHA512(key),
            "sha1" => new HMACSHA1(key),
            "md5" => new HMACMD5(key),
            _ => throw new ArgumentException($"unsupported algorithm \"{algorithm}\"", nameof(algorithm)),
        };
    }
}

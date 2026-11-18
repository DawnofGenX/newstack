using Xunit;

namespace {{ package_name }}.Tests;

public class CliTests
{
    private static (string Out, string Err, int Status) Capture(params string[] args)
    {
        var originalOut = Console.Out;
        var originalErr = Console.Error;
        using var output = new StringWriter();
        using var error = new StringWriter();
        Console.SetOut(output);
        Console.SetError(error);
        try
        {
            var status = HmacCli.Run(args);
            return (output.ToString(), error.ToString(), status);
        }
        finally
        {
            Console.SetOut(originalOut);
            Console.SetError(originalErr);
        }
    }

    [Fact]
    public void SignPrintsALowercaseHexDigest()
    {
        var result = Capture("sign", "--key", "secret", "--message", "payload");
        Assert.Equal(0, result.Status);
        Assert.Matches("^[0-9a-f]{64}$", result.Out.Trim());
    }

    [Fact]
    public void SignIsDeterministic()
    {
        var first = Capture("sign", "--key", "secret", "--message", "payload").Out;
        var second = Capture("sign", "--key", "secret", "--message", "payload").Out;
        Assert.Equal(first, second);
    }

    [Fact]
    public void VerifyRoundTripsASignature()
    {
        var digest = Capture("sign", "--key", "secret", "--message", "payload").Out.Trim();
        var matched = Capture("verify", "--key", "secret", "--message", "payload", "--digest", digest);
        Assert.Equal(0, matched.Status);
        Assert.Equal("match", matched.Out.Trim());
    }

    [Fact]
    public void VerifyExitsOneOnMismatch()
    {
        var result = Capture("verify", "--key", "other", "--message", "payload", "--digest", new string('a', 64));
        Assert.Equal(1, result.Status);
        Assert.Equal("mismatch", result.Out.Trim());
    }

    [Fact]
    public void AlgorithmChangesTheDigest()
    {
        var sha256 = Capture("sign", "--key", "secret", "--message", "payload").Out.Trim();
        var sha512 = Capture("sign", "--key", "secret", "--message", "payload", "--algo", "sha512").Out.Trim();
        Assert.NotEqual(sha256, sha512);
        Assert.Equal(128, sha512.Length);
    }

    [Fact]
    public void SignFilePrintsTheDigestAndPath()
    {
        var path = Path.GetTempFileName();
        try
        {
            File.WriteAllText(path, "payload");
            var result = Capture("sign-file", "--key", "secret", path);
            Assert.Equal(0, result.Status);
            Assert.EndsWith(path, result.Out.Trim());
        }
        finally
        {
            File.Delete(path);
        }
    }

    [Fact]
    public void MissingArgumentsExitTwo()
    {
        Assert.Equal(2, Capture().Status);
        Assert.Equal(2, Capture("frobnicate").Status);
        Assert.Equal(2, Capture("sign", "--key", "secret").Status);
        Assert.Equal(2, Capture("sign", "--message", "payload").Status);
        Assert.Equal(2, Capture("verify", "--key", "secret", "--message", "payload").Status);
        Assert.Equal(2, Capture("sign", "--key", "secret", "--message", "payload", "--algo", "sha3").Status);
    }

    [Fact]
    public void AMissingFileExitsOne()
    {
        var result = Capture("sign-file", "--key", "secret", "does-not-exist.txt");
        Assert.Equal(1, result.Status);
        Assert.Contains("cannot read", result.Err);
    }

    [Fact]
    public void HelpExitsZero()
    {
        var result = Capture("--help");
        Assert.Equal(0, result.Status);
        Assert.Contains("sign-file", result.Out);
    }
}

using Xunit;

namespace {{ package_name }}.Tests;

public class HmacTests
{
    // RFC 4231 test case 1: twenty 0x0b bytes keyed against "Hi There".
    private static readonly byte[] RfcKey = Enumerable.Repeat((byte)0x0b, 20).ToArray();

    [Fact]
    public void MatchesRfc4231ForSha256()
    {
        Assert.Equal(
            "b0344c61d8db38535ca8afceaf0bf12b881dc200c9833da726e9376c2e32cff7",
            Hmac.SignHex("sha256", "aaaaaaaaaaaaaaaaaaaa", "Hi There") is var _
                ? Convert.ToHexString(Hmac.Sign("sha256", RfcKey, "Hi There"u8.ToArray())).ToLowerInvariant()
                : string.Empty);
    }

    [Fact]
    public void MatchesRfc4231ForSha512()
    {
        Assert.Equal(
            "87aa7cdea5ef619d4ff0b4241a1d6cb02379f4e2ce4ec2787ad0b30545e17cde"
                + "daa833b7d6b8a702038b274eaea3f4e4be9d914eeb61f1702e696c203a126854",
            Convert.ToHexString(Hmac.Sign("sha512", RfcKey, "Hi There"u8.ToArray())).ToLowerInvariant());
    }

    [Fact]
    public void SignHexUsesUtf8()
    {
        var expected = Convert.ToHexString(
            Hmac.Sign("sha256", "secret"u8.ToArray(), "héllo"u8.ToArray())).ToLowerInvariant();
        Assert.Equal(expected, Hmac.SignHex("sha256", "secret", "héllo"));
    }

    [Fact]
    public void VerifiesAMatchingDigest()
    {
        var digest = Hmac.SignHex("sha256", "secret", "payload");
        Assert.True(Hmac.Verify("sha256", "secret"u8.ToArray(), "payload"u8.ToArray(), digest));
    }

    [Fact]
    public void RejectsAWrongDigest()
    {
        Assert.False(Hmac.Verify("sha256", "secret"u8.ToArray(), "payload"u8.ToArray(), new string('0', 64)));
    }

    [Fact]
    public void RejectsADigestThatIsNotHex()
    {
        Assert.False(Hmac.Verify("sha256", "secret"u8.ToArray(), "payload"u8.ToArray(), "not-hex"));
    }

    [Fact]
    public void EveryAlgorithmHasADistinctDigest()
    {
        var digests = Hmac.Algorithms
            .Select(algorithm => Hmac.SignHex(algorithm, "secret", "payload"))
            .ToArray();
        Assert.Equal(digests.Length, digests.Distinct().Count());
    }

    [Fact]
    public void RejectsAnUnknownAlgorithm()
    {
        Assert.Throws<ArgumentException>(() => Hmac.Sign("sha3", "secret"u8.ToArray(), "payload"u8.ToArray()));
    }
}

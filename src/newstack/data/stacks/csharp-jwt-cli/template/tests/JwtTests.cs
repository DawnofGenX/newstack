using System.Text.Json;
using Xunit;

namespace {{ package_name }}.Tests;

public class JwtTests
{
    [Fact]
    public void EncodeDecodeRoundTrip()
    {
        var token = Jwt.Encode(new Dictionary<string, string> { ["sub"] = "alice" }, "s3cr3t");
        var (header, payload) = Jwt.Decode(token);
        Assert.Contains("HS256", header);
        using var doc = JsonDocument.Parse(payload);
        Assert.Equal("alice", doc.RootElement.GetProperty("sub").GetString());
    }

    [Fact]
    public void VerifyValidToken()
    {
        var token = Jwt.Encode(new Dictionary<string, string> { ["sub"] = "alice" }, "s3cr3t");
        Assert.True(Jwt.Verify(token, "s3cr3t"));
    }

    [Fact]
    public void VerifyWrongSecretFails()
    {
        var token = Jwt.Encode(new Dictionary<string, string> { ["sub"] = "alice" }, "s3cr3t");
        Assert.False(Jwt.Verify(token, "other"));
    }

    [Fact]
    public void VerifyTamperedPayloadFails()
    {
        var token = Jwt.Encode(new Dictionary<string, string> { ["sub"] = "alice" }, "s3cr3t");
        var parts = token.Split('.');
        parts[1] = parts[1] + "x";
        Assert.False(Jwt.Verify(string.Join(".", parts), "s3cr3t"));
    }
}
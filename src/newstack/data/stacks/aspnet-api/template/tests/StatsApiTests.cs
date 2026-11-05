using System.Net;
using System.Net.Http.Json;
using System.Text.Json;
using Microsoft.AspNetCore.Mvc.Testing;

namespace {{ package_name }}.Tests;

/// <summary>
/// Boots the real application in memory, so these tests cover routing, model binding,
/// status codes and JSON shape — not just the counting function.
/// </summary>
public sealed class StatsApiTests : IClassFixture<WebApplicationFactory<Program>>
{
    private readonly HttpClient _client;

    public StatsApiTests(WebApplicationFactory<Program> factory) => _client = factory.CreateClient();

    [Fact]
    public async Task Health_reports_ok()
    {
        var response = await _client.GetAsync("/health");
        response.EnsureSuccessStatusCode();

        using var document = JsonDocument.Parse(await response.Content.ReadAsStringAsync());
        Assert.Equal("ok", document.RootElement.GetProperty("status").GetString());
    }

    [Fact]
    public async Task Get_counts_a_query_string()
    {
        var response = await _client.GetAsync("/stats?text=" + Uri.EscapeDataString("hello world\n"));

        Assert.Equal(("hello world\n", 1, 2, 12), await ReadCounts(response));
    }

    [Fact]
    public async Task Post_counts_a_json_body_exactly()
    {
        var response = await _client.PostAsJsonAsync("/stats", new { text = "a b\nc\n" });

        Assert.Equal(("a b\nc\n", 2, 3, 6), await ReadCounts(response));
    }

    [Fact]
    public async Task Text_comes_back_untouched()
    {
        // Trailing whitespace is data here; a framework that trims it makes the byte
        // count wrong, so the round-trip is part of the contract.
        var response = await _client.PostAsJsonAsync("/stats", new { text = "  padded  \n" });

        Assert.Equal(("  padded  \n", 1, 1, 11), await ReadCounts(response));
    }

    [Fact]
    public async Task Missing_text_is_a_422_not_a_crash()
    {
        var response = await _client.PostAsJsonAsync("/stats", new { });

        Assert.Equal(HttpStatusCode.UnprocessableEntity, response.StatusCode);
        using var document = JsonDocument.Parse(await response.Content.ReadAsStringAsync());
        Assert.Contains("text", document.RootElement.GetProperty("error").GetString());
    }

    [Fact]
    public async Task Null_text_is_a_422()
    {
        var response = await _client.PostAsJsonAsync("/stats", new { text = (string?)null });

        Assert.Equal(HttpStatusCode.UnprocessableEntity, response.StatusCode);
    }

    [Fact]
    public async Task Missing_query_parameter_is_a_422()
    {
        Assert.Equal(HttpStatusCode.UnprocessableEntity, (await _client.GetAsync("/stats")).StatusCode);
    }

    [Fact]
    public async Task Unknown_route_is_a_404()
    {
        Assert.Equal(HttpStatusCode.NotFound, (await _client.GetAsync("/nope")).StatusCode);
    }

    private static async Task<(string Text, int Lines, int Words, int Bytes)> ReadCounts(
        HttpResponseMessage response)
    {
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);

        using var document = JsonDocument.Parse(await response.Content.ReadAsStringAsync());
        var root = document.RootElement;
        return (
            root.GetProperty("text").GetString()!,
            root.GetProperty("lines").GetInt32(),
            root.GetProperty("words").GetInt32(),
            root.GetProperty("bytes").GetInt32());
    }
}

using System.Net;
using System.Net.Http.Json;
using Microsoft.AspNetCore.Mvc.Testing;
using Xunit;

namespace {{ package_name }}.Tests;

public class ApiTests : IClassFixture<WebApplicationFactory<Program>>
{
    private readonly HttpClient _client;

    public ApiTests(WebApplicationFactory<Program> factory)
    {
        _client = factory.CreateClient();
    }

    [Fact]
    public async Task Health_Returns_Ok()
    {
        var response = await _client.GetAsync("/health");
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        var body = await response.Content.ReadAsStringAsync();
        Assert.Contains("ok", body);
    }

    [Fact]
    public async Task Items_Can_Be_Created_And_Listed()
    {
        var post = await _client.PostAsJsonAsync("/items", new { Name = "widget" });
        Assert.Equal(HttpStatusCode.Created, post.StatusCode);

        var list = await _client.GetFromJsonAsync<List<string>>("/items");
        Assert.Contains("widget", list!);
    }
}

using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;

var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();

var items = new List<string>();

app.MapGet("/health", () => Results.Ok("ok"));

app.MapGet("/items", () => Results.Ok(items));

app.MapPost("/items", (ItemRequest req) =>
{
    if (string.IsNullOrWhiteSpace(req.Name))
    {
        return Results.BadRequest();
    }
    items.Add(req.Name);
    return Results.Created($"/items/{items.Count}", req.Name);
});

app.Run();

public record ItemRequest(string Name);

public partial class Program { }

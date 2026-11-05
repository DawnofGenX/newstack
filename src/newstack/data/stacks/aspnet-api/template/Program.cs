using System.Text.Json;
using {{ package_name }};

var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();

// Liveness. The verify step polls this before it sends any real traffic, so a
// failure here means the process never came up rather than a broken route.
app.MapGet("/health", () => Results.Json(new { status = "ok" }));

// GET /stats?text=... mirrors POST /stats for shell one-liners.
app.MapGet("/stats", (string? text) => text is null
    ? Unprocessable("the `text` query parameter is required")
    : Results.Json(Payload(text)));

// POST /stats {"text": "..."}: a missing or null field is the client's mistake, not a crash.
app.MapPost("/stats", (StatRequest? request) => request?.Text is null
    ? Unprocessable("the `text` field is required")
    : Results.Json(Payload(request.Text)));

app.Run();

static object Payload(string text)
{
    var counts = TextStat.Of(text);
    return new { text, lines = counts.Lines, words = counts.Words, bytes = counts.Bytes };
}

static IResult Unprocessable(string error) =>
    Results.Json(new { error }, statusCode: StatusCodes.Status422UnprocessableEntity);

// WebApplicationFactory<Program> needs a public entry type; top-level statements
// leave the generated Program class internal, so declare one.
public partial class Program
{
}

// Bound from the request body. Nullable on purpose: "text": null must be a 422, not a 400.
public sealed record StatRequest(string? Text);

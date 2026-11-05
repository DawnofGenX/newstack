/// The route table, pure: method/path/query/body in, status and body out.
module textstat.contract;

import std.array : replace;
import std.conv : to;
import std.uri : decode;

import textstat.counts : countText;
import textstat.json : TextKind, readText;

struct Reply
{
    int status;
    string body;
}

/// Answers one request without touching a socket, so every status code is testable.
Reply route(string method, string path, string query, string body)
{
    if (path == "/health")
    {
        if (method == "GET")
            return Reply(200, `{"status":"ok"}`);
        return Reply(405, errorJson("method_not_allowed", null));
    }
    if (path == "/stats")
    {
        if (method == "GET")
        {
            bool present;
            auto text = queryParam(query, "text", present);
            if (!present)
                return Reply(422, errorJson("missing_text", null));
            return statsReply(text);
        }
        if (method == "POST")
        {
            string text;
            final switch (readText(body, text))
            {
            case TextKind.text:
                return statsReply(text);
            case TextKind.missing:
                return Reply(422, errorJson("missing_text", null));
            case TextKind.invalid:
                return Reply(422, errorJson("invalid_json", null));
            }
        }
        return Reply(405, errorJson("method_not_allowed", null));
    }
    return Reply(404, errorJson("not_found", "no route for " ~ method ~ " " ~ path));
}

private Reply statsReply(string text)
{
    auto counts = countText(text);
    return Reply(200, `{"text":` ~ jsonQuote(text) ~ `,"lines":` ~ to!string(counts.lines) ~
        `,"words":` ~ to!string(counts.words) ~ `,"bytes":` ~ to!string(counts.bytes) ~ `}`);
}

private string errorJson(string error, string detail)
{
    if (detail is null)
        return `{"error":` ~ jsonQuote(error) ~ `}`;
    return `{"error":` ~ jsonQuote(error) ~ `,"detail":` ~ jsonQuote(detail) ~ `}`;
}

private string jsonQuote(string text)
{
    string out_;
    out_.reserve(text.length + 2);
    out_ ~= '"';
    foreach (char character; text)
    {
        switch (character)
        {
        case '"':
            out_ ~= `\"`;
            break;
        case '\\':
            out_ ~= `\\`;
            break;
        case '\n':
            out_ ~= `\n`;
            break;
        case '\r':
            out_ ~= `\r`;
            break;
        case '\t':
            out_ ~= `\t`;
            break;
        default:
            if (character < 0x20)
                out_ ~= `\u00` ~ "0123456789abcdef"[character >> 4] ~ "0123456789abcdef"[character & 0xF];
            else
                out_ ~= character;
        }
    }
    out_ ~= '"';
    return out_;
}

/// Reads one `&`/`=` query pair, decoding `+` and `%XX`.
private string queryParam(string query, string name, out bool present)
{
    present = false;
    if (query.length == 0)
        return "";
    size_t index = 0;
    while (index <= query.length)
    {
        auto end = index;
        while (end < query.length && query[end] != '&')
            end++;
        auto pair = query[index .. end];
        auto equals = pair.length;
        foreach (i, character; pair)
        {
            if (character == '=')
            {
                equals = i;
                break;
            }
        }
        if (equals < pair.length && pair[0 .. equals] == name)
        {
            present = true;
            return decode(pair[equals + 1 .. $].replace("+", " "));
        }
        if (end >= query.length)
            break;
        index = end + 1;
    }
    return "";
}

unittest
{
    assert(route("GET", "/health", "", "") == Reply(200, `{"status":"ok"}`));
    assert(route("GET", "/stats", "text=hello%20world%0A", "").body ==
        `{"text":"hello world\n","lines":1,"words":2,"bytes":12}`);
    assert(route("POST", "/stats", "", `{"text":"a b\nc\n"}`).body ==
        `{"text":"a b\nc\n","lines":2,"words":3,"bytes":6}`);
    assert(route("GET", "/stats", "", "").status == 422);
    assert(route("GET", "/stats", "text=", "").body == `{"text":"","lines":0,"words":0,"bytes":0}`);
    assert(route("POST", "/stats", "", `{}`).status == 422);
    assert(route("POST", "/stats", "", `nope`).status == 422);
    assert(route("POST", "/stats", "", `{"text":42}`).status == 422);
    assert(route("DELETE", "/health", "", "").status == 405);
    assert(route("PUT", "/stats", "text=a", "").status == 405);
    auto missing = route("GET", "/nope", "", "");
    assert(missing.status == 404);
    assert(missing.body == `{"error":"not_found","detail":"no route for GET /nope"}`);
    assert(route("GET", "/stats", "other=1&text=hi", "").body ==
        `{"text":"hi","lines":0,"words":1,"bytes":2}`);
    assert(route("GET", "/stats", "text=a+b", "").body ==
        `{"text":"a b","lines":0,"words":2,"bytes":3}`);
}

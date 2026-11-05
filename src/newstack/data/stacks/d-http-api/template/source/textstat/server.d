/// A blocking HTTP/1.1 loop on std.socket, one request per connection.
module textstat.server;

import core.sys.posix.signal : SIG_IGN, SIGPIPE, signal;
import std.conv : to;
import std.socket;
import std.stdio : stderr, stdout, writeln;
import std.string : indexOf, split, strip, toLower;

import textstat.contract : Reply, route;

private enum size_t maxHeader = 8192;
private enum size_t maxBody = 65536;

struct Request
{
    string method;
    string path;
    string query;
    string body;
}

private struct Parsed
{
    bool ok;
    bool tooLarge;
    Request request;
}

/// Reads one request off a socket: the head first, then exactly Content-Length bytes.
private Parsed readRequest(Socket connection)
{
    ubyte[4096] buffer;
    string raw;
    size_t blank = size_t.max;
    while (raw.length < maxHeader)
    {
        auto count = connection.receive(buffer[]);
        if (count <= 0)
            break;
        raw ~= cast(string) buffer[0 .. count];
        auto found = raw.indexOf("\r\n\r\n");
        if (found >= 0)
        {
            blank = cast(size_t) found;
            break;
        }
    }
    Parsed parsed;
    if (blank == size_t.max)
        return parsed;
    auto lines = raw[0 .. blank].split("\r\n");
    if (lines.length == 0)
        return parsed;
    auto parts = lines[0].split(" ");
    if (parts.length < 2)
        return parsed;

    Request request;
    request.method = parts[0];
    auto target = parts[1];
    auto question = target.indexOf('?');
    if (question < 0)
    {
        request.path = target;
    }
    else
    {
        request.path = target[0 .. question];
        request.query = target[question + 1 .. $];
    }

    size_t length;
    foreach (line; lines[1 .. $])
    {
        auto colon = line.indexOf(':');
        if (colon < 0)
            continue;
        if (line[0 .. colon].toLower == "content-length")
            length = to!size_t(line[colon + 1 .. $].strip);
    }
    if (length > maxBody)
    {
        parsed.tooLarge = true;
        parsed.request = request;
        return parsed;
    }

    request.body = raw[blank + 4 .. $];
    if (request.body.length > length)
        request.body = request.body[0 .. length];
    while (request.body.length < length)
    {
        auto count = connection.receive(buffer[]);
        if (count <= 0)
            break;
        request.body ~= cast(string) buffer[0 .. count];
    }
    if (request.body.length > length)
        request.body = request.body[0 .. length];

    parsed.ok = true;
    parsed.request = request;
    return parsed;
}

private string statusText(int status)
{
    final switch (status)
    {
    case 200:
        return "OK";
    case 404:
        return "Not Found";
    case 405:
        return "Method Not Allowed";
    case 413:
        return "Payload Too Large";
    case 422:
        return "Unprocessable Entity";
    case 500:
        return "Internal Server Error";
    }
}

private void respond(Socket connection, Reply reply)
{
    auto header = "HTTP/1.1 " ~ to!string(reply.status) ~ " " ~ statusText(reply.status) ~ "\r\n" ~
        "content-type: application/json\r\n" ~
        "content-length: " ~ to!string(reply.body.length) ~ "\r\n" ~
        "connection: close\r\n\r\n";
    connection.send(header);
    if (reply.body.length > 0)
        connection.send(reply.body);
}

/// Serves until the process is killed; SIGPIPE is ignored so a lost client is not fatal.
void serve(string host, ushort port)
{
    signal(SIGPIPE, SIG_IGN);
    auto listener = new TcpSocket();
    scope (exit)
        listener.close();
    listener.setOption(SocketOptionLevel.SOCKET, SocketOption.REUSEADDR, 1);
    listener.bind(new InternetAddress(host, port));
    listener.listen(16);
    writeln("listening on http://", host, ":", port);
    stdout.flush();
    while (true)
    {
        auto connection = listener.accept();
        if (connection is null)
            continue;
        scope (exit)
            connection.close();
        try
        {
            auto parsed = readRequest(connection);
            if (parsed.tooLarge)
            {
                respond(connection, Reply(413, `{"error":"body_too_large"}`));
                continue;
            }
            if (!parsed.ok)
            {
                respond(connection, Reply(422, `{"error":"bad_request"}`));
                continue;
            }
            respond(connection, route(parsed.request.method, parsed.request.path,
                parsed.request.query, parsed.request.body));
        }
        catch (Exception error)
        {
            stderr.writeln("request failed: ", error.msg);
            stderr.flush();
        }
    }
}

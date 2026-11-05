/// Reads PORT/HOST from the environment and serves until killed.
module app;

import std.conv : to;
import std.process : environment;

import textstat.server : serve;

void main()
{
    auto host = environment.get("HOST", "127.0.0.1");
    auto port = environment.get("PORT", "8080");
    serve(host, to!ushort(port));
}

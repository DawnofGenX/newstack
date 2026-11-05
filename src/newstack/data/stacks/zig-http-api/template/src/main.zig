//! `{{ title }}` — a JSON service over std.http.
//!
//! This file only wires the process together: read PORT/ADDR, bind, serve.

const std = @import("std");
const server = @import("server.zig");

pub const default_port: u16 = 8080;

pub fn main(init: std.process.Init) !void {
    const io = init.io;
    const gpa = init.gpa;

    var port: u16 = default_port;
    if (init.environ_map.get("PORT")) |raw| {
        port = std.fmt.parseInt(u16, raw, 10) catch default_port;
    }
    const host = init.environ_map.get("ADDR") orelse "127.0.0.1";

    const address = try std.Io.net.IpAddress.parse(host, port);
    // `reuse_address` keeps a restart from failing on the previous socket's
    // TIME_WAIT leftovers; without it a second start within a minute is an
    // AddressInUse error.
    var listener = try address.listen(io, .{ .reuse_address = true });

    std.debug.print("listening on http://{s}:{d}\n", .{ host, port });
    try server.serve(io, gpa, &listener);
}

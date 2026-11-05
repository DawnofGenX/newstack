//! The socket layer: accept a connection, turn the wire bytes into a
//! `contract.Request`, send the reply. Zig 0.17's `std.http.Server` works on
//! `Io.Reader`/`Io.Writer` interfaces, not on a stream, so this file owns the
//! buffers and the request loop.

const std = @import("std");
const contract = @import("contract.zig");

const max_body = 64 * 1024;

pub fn serve(io: std.Io, gpa: std.mem.Allocator, listener: *std.Io.net.Server) !void {
    while (true) {
        const stream = listener.accept(io) catch |err| switch (err) {
            error.ConnectionAborted => continue,
            else => return err,
        };
        handleConnection(io, gpa, stream) catch |err| {
            std.log.warn("connection failed: {s}", .{@errorName(err)});
        };
        stream.close(io);
    }
}

fn handleConnection(io: std.Io, gpa: std.mem.Allocator, stream: std.Io.net.Stream) !void {
    var read_buffer: [8192]u8 = undefined;
    var write_buffer: [8192]u8 = undefined;
    var stream_reader = stream.reader(io, &read_buffer);
    var stream_writer = stream.writer(io, &write_buffer);
    var server = std.http.Server.init(&stream_reader.interface, &stream_writer.interface);

    var request = server.receiveHead() catch return;
    const target = request.head.target;

    const question = std.mem.findScalar(u8, target, '?');
    const path = if (question) |index| target[0..index] else target;
    const query = if (question) |index| target[index + 1 ..] else "";

    var body: []const u8 = "";
    defer if (body.len != 0) gpa.free(body);
    if (request.head.method == .POST) {
        var body_buffer: [16 * 1024]u8 = undefined;
        const body_reader = request.readerExpectNone(&body_buffer);
        body = body_reader.allocRemaining(gpa, .limited(max_body)) catch return;
    }

    var arena_state = std.heap.ArenaAllocator.init(gpa);
    defer arena_state.deinit();
    const arena = arena_state.allocator();

    const reply: contract.Reply = contract.route(arena, .{
        .method = @tagName(request.head.method),
        .path = path,
        .query = query,
        .body = body,
    }) catch .{ .status = 500, .body = "{\"error\":\"internal_error\"}" };

    const status: std.http.Status = switch (reply.status) {
        200 => .ok,
        404 => .not_found,
        405 => .method_not_allowed,
        422 => .unprocessable_entity,
        else => .internal_server_error,
    };
    try request.respond(reply.body, .{
        .status = status,
        .extra_headers = &.{
            .{ .name = "content-type", .value = "application/json" },
            .{ .name = "connection", .value = "close" },
        },
    });
}

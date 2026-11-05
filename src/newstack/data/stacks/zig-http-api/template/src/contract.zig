//! Pure request handling: no sockets, no globals. `server.zig` reads the wire
//! bytes; everything that decides the answer lives here so it can be tested.

const std = @import("std");
const counting = @import("counting.zig");

pub const Reply = struct {
    status: u16,
    body: []const u8,
};

pub const Request = struct {
    method: []const u8,
    path: []const u8,
    query: []const u8,
    body: []const u8,
};

fn escapeJson(arena: std.mem.Allocator, text: []const u8) ![]const u8 {
    var out: std.Io.Writer.Allocating = .init(arena);
    errdefer out.deinit();
    const w = &out.writer;
    for (text) |byte| {
        switch (byte) {
            '"' => w.writeAll("\\\"") catch return error.OutOfMemory,
            '\\' => w.writeAll("\\\\") catch return error.OutOfMemory,
            '\n' => w.writeAll("\\n") catch return error.OutOfMemory,
            '\r' => w.writeAll("\\r") catch return error.OutOfMemory,
            '\t' => w.writeAll("\\t") catch return error.OutOfMemory,
            else => if (byte < 0x20)
                w.print("\\u{x:0>4}", .{byte}) catch return error.OutOfMemory
            else
                w.writeByte(byte) catch return error.OutOfMemory,
        }
    }
    return try out.toOwnedSlice();
}

/// `{"text": "...", "lines": n, "words": n, "bytes": n}`, the shape every
/// endpoint in this starter returns.
pub fn countsJson(arena: std.mem.Allocator, text: []const u8, counts: counting.Counts) ![]const u8 {
    const escaped = try escapeJson(arena, text);
    return std.fmt.allocPrint(arena, "{{\"text\":\"{s}\",\"lines\":{d},\"words\":{d},\"bytes\":{d}}}", .{
        escaped, counts.lines, counts.words, counts.bytes,
    });
}

fn errorJson(arena: std.mem.Allocator, code: []const u8) ![]const u8 {
    return std.fmt.allocPrint(arena, "{{\"error\":\"{s}\"}}", .{code});
}

/// Value of `name` in a raw query string (`a=1&b=2`), percent-decoded.
pub fn queryParam(arena: std.mem.Allocator, query: []const u8, name: []const u8) !?[]const u8 {
    var it = std.mem.splitScalar(u8, query, '&');
    while (it.next()) |pair| {
        const eq = std.mem.findScalar(u8, pair, '=') orelse continue;
        if (!std.mem.eql(u8, pair[0..eq], name)) continue;
        const raw = pair[eq + 1 ..];
        // Decode a copy: percentDecodeInPlace rewrites the buffer it is given.
        const buffer = try arena.dupe(u8, raw);
        return std.Uri.percentDecodeInPlace(buffer);
    }
    return null;
}

pub fn route(arena: std.mem.Allocator, request: Request) !Reply {
    const is_health = std.mem.eql(u8, request.path, "/health");
    const is_stats = std.mem.eql(u8, request.path, "/stats");

    if (!is_health and !is_stats) {
        return .{
            .status = 404,
            .body = try std.fmt.allocPrint(arena, "{{\"error\":\"not_found\",\"detail\":\"no route for {s} {s}\"}}", .{
                request.method, request.path,
            }),
        };
    }

    if (is_health) {
        if (!std.mem.eql(u8, request.method, "GET")) {
            return .{ .status = 405, .body = try errorJson(arena, "method_not_allowed") };
        }
        return .{ .status = 200, .body = "{\"status\":\"ok\"}" };
    }

    if (std.mem.eql(u8, request.method, "GET")) {
        const text = (try queryParam(arena, request.query, "text")) orelse
            return .{ .status = 422, .body = try errorJson(arena, "missing_text") };
        return .{ .status = 200, .body = try countsJson(arena, text, counting.count(text)) };
    }

    if (std.mem.eql(u8, request.method, "POST")) {
        const text = postText(arena, request.body) catch |err| switch (err) {
            error.InvalidJson => return .{ .status = 422, .body = try errorJson(arena, "invalid_json") },
            error.MissingText => return .{ .status = 422, .body = try errorJson(arena, "missing_text") },
            error.OutOfMemory => return error.OutOfMemory,
        };
        return .{ .status = 200, .body = try countsJson(arena, text, counting.count(text)) };
    }

    return .{ .status = 405, .body = try errorJson(arena, "method_not_allowed") };
}

const PostBodyError = error{ InvalidJson, MissingText, OutOfMemory };

/// The `text` field of a `{"text": "..."}` body.
fn postText(arena: std.mem.Allocator, body: []const u8) PostBodyError![]const u8 {
    const parsed = std.json.parseFromSlice(std.json.Value, arena, body, .{}) catch
        return error.InvalidJson;
    return switch (parsed.value) {
        .object => |object| switch (object.get("text") orelse return error.MissingText) {
            .string => |text| text,
            else => error.MissingText,
        },
        else => error.InvalidJson,
    };
}

test "health is 200" {
    var arena_state = std.heap.ArenaAllocator.init(std.testing.allocator);
    defer arena_state.deinit();
    const arena = arena_state.allocator();
    const reply = try route(arena, .{ .method = "GET", .path = "/health", .query = "", .body = "" });
    try std.testing.expectEqual(@as(u16, 200), reply.status);
    try std.testing.expectEqualStrings("{\"status\":\"ok\"}", reply.body);
}

test "health rejects other methods" {
    var arena_state = std.heap.ArenaAllocator.init(std.testing.allocator);
    defer arena_state.deinit();
    const arena = arena_state.allocator();
    const reply = try route(arena, .{ .method = "DELETE", .path = "/health", .query = "", .body = "" });
    try std.testing.expectEqual(@as(u16, 405), reply.status);
}

test "get stats counts the decoded text" {
    var arena_state = std.heap.ArenaAllocator.init(std.testing.allocator);
    defer arena_state.deinit();
    const arena = arena_state.allocator();
    const reply = try route(arena, .{
        .method = "GET",
        .path = "/stats",
        .query = "text=hello%20world%0A",
        .body = "",
    });
    try std.testing.expectEqual(@as(u16, 200), reply.status);
    try std.testing.expectEqualStrings("{\"text\":\"hello world\\n\",\"lines\":1,\"words\":2,\"bytes\":12}", reply.body);
}

test "get stats without text is 422" {
    var arena_state = std.heap.ArenaAllocator.init(std.testing.allocator);
    defer arena_state.deinit();
    const arena = arena_state.allocator();
    const reply = try route(arena, .{ .method = "GET", .path = "/stats", .query = "other=1", .body = "" });
    try std.testing.expectEqual(@as(u16, 422), reply.status);
    try std.testing.expectEqualStrings("{\"error\":\"missing_text\"}", reply.body);
}

test "post stats counts the text it was sent" {
    var arena_state = std.heap.ArenaAllocator.init(std.testing.allocator);
    defer arena_state.deinit();
    const arena = arena_state.allocator();
    const reply = try route(arena, .{
        .method = "POST",
        .path = "/stats",
        .query = "",
        .body = "{\"text\":\"a b\\nc\\n\"}",
    });
    try std.testing.expectEqual(@as(u16, 200), reply.status);
    try std.testing.expectEqualStrings("{\"text\":\"a b\\nc\\n\",\"lines\":2,\"words\":3,\"bytes\":6}", reply.body);
}

test "post stats rejects a non-object body" {
    var arena_state = std.heap.ArenaAllocator.init(std.testing.allocator);
    defer arena_state.deinit();
    const arena = arena_state.allocator();
    const reply = try route(arena, .{ .method = "POST", .path = "/stats", .query = "", .body = "nope" });
    try std.testing.expectEqual(@as(u16, 422), reply.status);
    try std.testing.expectEqualStrings("{\"error\":\"invalid_json\"}", reply.body);
}

test "post stats rejects a non-string text" {
    var arena_state = std.heap.ArenaAllocator.init(std.testing.allocator);
    defer arena_state.deinit();
    const arena = arena_state.allocator();
    const reply = try route(arena, .{ .method = "POST", .path = "/stats", .query = "", .body = "{\"text\":42}" });
    try std.testing.expectEqual(@as(u16, 422), reply.status);
    try std.testing.expectEqualStrings("{\"error\":\"missing_text\"}", reply.body);
}

test "an unknown route is a json 404" {
    var arena_state = std.heap.ArenaAllocator.init(std.testing.allocator);
    defer arena_state.deinit();
    const arena = arena_state.allocator();
    const reply = try route(arena, .{ .method = "GET", .path = "/nope", .query = "", .body = "" });
    try std.testing.expectEqual(@as(u16, 404), reply.status);
    try std.testing.expectEqualStrings("{\"error\":\"not_found\",\"detail\":\"no route for GET /nope\"}", reply.body);
}

test "utf-8 counts bytes, not characters" {
    var arena_state = std.heap.ArenaAllocator.init(std.testing.allocator);
    defer arena_state.deinit();
    const arena = arena_state.allocator();
    const reply = try route(arena, .{
        .method = "GET",
        .path = "/stats",
        .query = "text=h%C3%A9llo%20w%C3%B6rld%0A",
        .body = "",
    });
    try std.testing.expectEqual(@as(u16, 200), reply.status);
    try std.testing.expect(std.mem.endsWith(u8, reply.body, "\"lines\":1,\"words\":2,\"bytes\":14}"));
}

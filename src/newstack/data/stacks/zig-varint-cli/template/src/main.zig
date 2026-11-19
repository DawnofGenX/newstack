const std = @import("std");
const varint = @import("varint.zig");

pub const program_name = "{{ package_name }}";

pub const usage_text =
    \\Usage: {s} <command> [args]
    \\
    \\Commands:
    \\  encode <n>        print unsigned LEB128 bytes (space separated)
    \\  decode <b...>     decode bytes (space or comma separated) to a number
    \\  -h, --help        show this help
    \\
;

pub fn main(init: std.process.Init) !void {
    const arena = init.arena.allocator();
    const io = init.io;
    const argv = try init.minimal.args.toSlice(arena);
    const args = try arena.alloc([]const u8, argv.len);
    for (argv, 0..) |arg, index| args[index] = arg;
    const rest = if (args.len > 0) args[1..] else args;

    var stdout_buffer: [4096]u8 = undefined;
    var stdout_writer: std.Io.File.Writer = .init(.stdout(), io, &stdout_buffer);
    const out = &stdout_writer.interface;

    var stderr_buffer: [4096]u8 = undefined;
    var stderr_writer: std.Io.File.Writer = .init(.stderr(), io, &stderr_buffer);
    const err = &stderr_writer.interface;

    if (rest.len == 0) {
        err.print(usage_text, .{program_name}) catch {};
        err.flush() catch {};
        std.process.exit(2);
    }
    if (std.mem.eql(u8, rest[0], "-h") or std.mem.eql(u8, rest[0], "--help")) {
        try out.print(usage_text, .{program_name});
        try out.flush();
        return;
    }
    if (std.mem.eql(u8, rest[0], "encode")) {
        if (rest.len != 2) {
            err.print("usage: {s} encode <n>\n", .{program_name}) catch {};
            err.flush() catch {};
            std.process.exit(2);
        }
        const value = std.fmt.parseUnsigned(u64, rest[1], 10) catch {
            err.print("invalid number: {s}\n", .{rest[1]}) catch {};
            err.flush() catch {};
            std.process.exit(2);
        };
        var buf: [10]u8 = undefined;
        const n = varint.encodeUleb128(value, &buf);
        for (buf[0..n], 0..) |b, i| {
            if (i > 0) try out.writeAll(" ");
            var tmp: [4]u8 = undefined;
            const s = try std.fmt.bufPrint(&tmp, "{d}", .{b});
            try out.writeAll(s);
        }
        try out.writeAll("\n");
        try out.flush();
        return;
    }
    if (std.mem.eql(u8, rest[0], "decode")) {
        if (rest.len < 2) {
            err.print("usage: {s} decode <bytes...>\n", .{program_name}) catch {};
            err.flush() catch {};
            std.process.exit(2);
        }
        var bytes: [16]u8 = undefined;
        var count: usize = 0;
        for (rest[1..]) |tok| {
            var it = std.mem.splitScalar(u8, tok, ',');
            while (it.next()) |part| {
                if (part.len == 0) continue;
                const b = std.fmt.parseUnsigned(u8, part, 10) catch {
                    err.print("invalid byte: {s}\n", .{part}) catch {};
                    err.flush() catch {};
                    std.process.exit(2);
                };
                if (count >= bytes.len) {
                    err.print("too many bytes\n", .{}) catch {};
                    err.flush() catch {};
                    std.process.exit(2);
                }
                bytes[count] = b;
                count += 1;
            }
        }
        const r = varint.decodeUleb128(bytes[0..count]) catch {
            err.print("decode error\n", .{}) catch {};
            err.flush() catch {};
            std.process.exit(1);
        };
        var tmp: [32]u8 = undefined;
        const s = try std.fmt.bufPrint(&tmp, "{d}\n", .{r.value});
        try out.writeAll(s);
        try out.flush();
        return;
    }
    err.print("unknown command: {s}\n", .{rest[0]}) catch {};
    err.print(usage_text, .{program_name}) catch {};
    err.flush() catch {};
    std.process.exit(2);
}
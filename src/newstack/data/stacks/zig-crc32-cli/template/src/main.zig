//! `{{ title }}` — CRC-32 of a string or a file.
//!
//! Thin layer: this file owns argv, exit codes and printing. The checksum
//! itself lives in `crc32.zig`.

const std = @import("std");
const Io = std.Io;
const crc = @import("crc32.zig");

pub const program_name = "{{ package_name }}";

pub const usage_text =
    \\Usage: {s} --string TEXT [--check HEX]
    \\       {s} --file PATH [--check HEX]
    \\
    \\Prints the CRC-32 (IEEE 802.3, as used by gzip and zlib) of the given
    \\text or file as eight lower-case hex digits.
    \\
    \\Options:
    \\  --string TEXT  checksum of the text itself
    \\  --file PATH    checksum of the file contents
    \\  --check HEX    compare against an expected checksum
    \\  -h, --help     show this help and exit
    \\
    \\Exit codes:
    \\  0  success (including a matching --check)
    \\  1  the file cannot be read, or --check does not match
    \\  2  usage error (missing input, unknown flag, bad hex)
    \\
;

pub const Input = union(enum) {
    text: []const u8,
    file: []const u8,
};

pub const Config = struct {
    input: Input,
    check: ?[]const u8 = null,
};

pub const Command = union(enum) {
    help,
    usage: []const u8,
    run: Config,
};

fn isHexDigit(byte: u8) bool {
    return (byte >= '0' and byte <= '9') or (byte >= 'a' and byte <= 'f') or (byte >= 'A' and byte <= 'F');
}

/// Decides what to do from the arguments after the program name. Pure: no
/// printing, no exits, so the tests drive it directly.
pub fn parse(args: []const []const u8) Command {
    var input: ?Input = null;
    var check: ?[]const u8 = null;

    var index: usize = 0;
    while (index < args.len) : (index += 1) {
        const arg = args[index];
        if (std.mem.eql(u8, arg, "--help") or std.mem.eql(u8, arg, "-h")) return .help;
        const takes_value = std.mem.eql(u8, arg, "--string")
            or std.mem.eql(u8, arg, "--file")
            or std.mem.eql(u8, arg, "--check");
        if (!takes_value) return .{ .usage = "unknown option or argument" };
        if (index + 1 >= args.len) return .{ .usage = "option needs a value" };
        index += 1;
        const value = args[index];
        if (std.mem.eql(u8, arg, "--string")) {
            if (input != null) return .{ .usage = "give either --string or --file, not both" };
            input = .{ .text = value };
        } else if (std.mem.eql(u8, arg, "--file")) {
            if (input != null) return .{ .usage = "give either --string or --file, not both" };
            input = .{ .file = value };
        } else {
            if (value.len != 8) return .{ .usage = "--check needs eight hex digits" };
            for (value) |byte| {
                if (!isHexDigit(byte)) return .{ .usage = "--check needs eight hex digits" };
            }
            check = value;
        }
    }

    const chosen = input orelse return .{ .usage = "missing --string or --file" };
    return .{ .run = .{ .input = chosen, .check = check } };
}

fn tagOf(command: Command) std.meta.Tag(Command) {
    return std.meta.activeTag(command);
}

pub fn main(init: std.process.Init) !void {
    const arena = init.arena.allocator();
    const io = init.io;
    const argv = try init.minimal.args.toSlice(arena);

    const args = try arena.alloc([]const u8, argv.len);
    for (argv, 0..) |arg, index| args[index] = arg;
    const rest = if (args.len > 0) args[1..] else args;

    var stdout_buffer: [4096]u8 = undefined;
    var stdout_writer: Io.File.Writer = .init(.stdout(), io, &stdout_buffer);
    const out = &stdout_writer.interface;

    var stderr_buffer: [4096]u8 = undefined;
    var stderr_writer: Io.File.Writer = .init(.stderr(), io, &stderr_buffer);
    const err = &stderr_writer.interface;

    const config = switch (parse(rest)) {
        .help => {
            try out.print(usage_text, .{ program_name, program_name });
            try out.flush();
            return;
        },
        .usage => |reason| {
            err.print("{s}: {s}\n\n", .{ program_name, reason }) catch {};
            err.print(usage_text, .{ program_name, program_name }) catch {};
            err.flush() catch {};
            std.process.exit(2);
        },
        .run => |run| run,
    };

    const data: []const u8 = switch (config.input) {
        .text => |value| value,
        .file => |path| std.Io.Dir.cwd().readFileAlloc(io, path, arena, .limited(64 * 1024 * 1024)) catch {
            err.print("{s}: cannot read {s}\n", .{ program_name, path }) catch {};
            err.flush() catch {};
            std.process.exit(1);
        },
    };

    const value = crc.hash(data);
    var hex_buffer: [8]u8 = undefined;
    const hex = crc.toHex(&hex_buffer, value);

    if (config.check) |expected| {
        if (std.ascii.eqlIgnoreCase(expected, hex)) {
            out.print("ok {s}\n", .{hex}) catch std.process.exit(1);
            out.flush() catch std.process.exit(1);
            return;
        }
        err.print("{s}: checksum mismatch: expected {s}, got {s}\n", .{ program_name, expected, hex }) catch {};
        err.flush() catch {};
        std.process.exit(1);
    }

    out.print("{s}\n", .{hex}) catch std.process.exit(1);
    out.flush() catch std.process.exit(1);
}

test "a bare command line is a usage error" {
    try std.testing.expectEqual(std.meta.Tag(Command).usage, tagOf(parse(&.{})));
}

test "--help and -h ask for help" {
    try std.testing.expectEqual(std.meta.Tag(Command).help, tagOf(parse(&.{"--help"})));
    try std.testing.expectEqual(std.meta.Tag(Command).help, tagOf(parse(&.{"-h"})));
}

test "an unknown flag is a usage error" {
    try std.testing.expectEqual(std.meta.Tag(Command).usage, tagOf(parse(&.{ "--string", "x", "--bogus" })));
}

test "both --string and --file is a usage error" {
    try std.testing.expectEqual(std.meta.Tag(Command).usage, tagOf(parse(&.{ "--string", "x", "--file", "y" })));
}

test "a short or non-hex --check is a usage error" {
    try std.testing.expectEqual(std.meta.Tag(Command).usage, tagOf(parse(&.{ "--string", "x", "--check", "abc" })));
    try std.testing.expectEqual(std.meta.Tag(Command).usage, tagOf(parse(&.{ "--string", "x", "--check", "zzzzzzzz" })));
}

test "a run carries its input and expected checksum" {
    const command = parse(&.{ "--string", "123456789", "--check", "cbf43926" });
    try std.testing.expectEqual(std.meta.Tag(Command).run, tagOf(command));
    try std.testing.expectEqualStrings("123456789", command.run.input.text);
    try std.testing.expectEqualStrings("cbf43926", command.run.check.?);
}

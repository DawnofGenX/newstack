//! `{{ title }}` — a wc-style counter.
//!
//! Thin layer: this file owns argv, exit codes and stdio. All the counting
//! lives in `counting.zig`.

const std = @import("std");
const Io = std.Io;
const counting = @import("counting.zig");

/// Executable name, also used in the usage text and error messages.
pub const program_name = "{{ package_name }}";

pub const usage_text =
    \\Usage: {s} [OPTIONS] <FILE>
    \\
    \\Count lines, words and bytes in FILE, wc-style.
    \\
    \\Options:
    \\  -h, --help    Show this help and exit
    \\
    \\Exit codes:
    \\  0  success (or --help)
    \\  1  FILE could not be read
    \\  2  usage error (unknown flag, missing or extra arguments)
    \\
;

pub const Command = union(enum) {
    help,
    usage: []const u8,
    count: []const u8,
};

/// Decide what to do from the arguments *after* the program name.
pub fn parse(args: []const []const u8) Command {
    var path: ?[]const u8 = null;
    for (args) |arg| {
        if (std.mem.eql(u8, arg, "--help") or std.mem.eql(u8, arg, "-h")) return .help;
        if (arg.len > 0 and arg[0] == '-') return .{ .usage = "unknown option" };
        if (path != null) return .{ .usage = "expected exactly one FILE" };
        path = arg;
    }
    return if (path) |p| .{ .count = p } else .{ .usage = "missing FILE" };
}

fn tagOf(command: Command) std.meta.Tag(Command) {
    return std.meta.activeTag(command);
}

pub fn main(init: std.process.Init) !void {
    const arena = init.arena.allocator();
    const io = init.io;
    const argv = try init.minimal.args.toSlice(arena);

    // argv[0] is the program name; `parse` only wants what is left. Copy into a
    // plain slice because argv elements are sentinel-terminated.
    const args = try arena.alloc([]const u8, argv.len);
    for (argv, 0..) |arg, index| args[index] = arg;
    const rest = if (args.len > 0) args[1..] else args;

    var stdout_buffer: [4096]u8 = undefined;
    var stdout_writer: Io.File.Writer = .init(.stdout(), io, &stdout_buffer);
    const out = &stdout_writer.interface;

    var stderr_buffer: [4096]u8 = undefined;
    var stderr_writer: Io.File.Writer = .init(.stderr(), io, &stderr_buffer);
    const err = &stderr_writer.interface;

    switch (parse(rest)) {
        .help => {
            try out.print(usage_text, .{program_name});
            try out.flush();
        },
        .usage => |reason| {
            err.print("{s}: {s}\n\n", .{ program_name, reason }) catch {};
            err.print(usage_text, .{program_name}) catch {};
            err.flush() catch {};
            std.process.exit(2);
        },
        .count => |path| {
            const data = Io.Dir.cwd().readFileAlloc(io, path, arena, .unlimited) catch {
                err.print("{s}: cannot read {s}\n", .{ program_name, path }) catch {};
                err.flush() catch {};
                std.process.exit(1);
            };
            const counts = counting.count(data);
            out.print("{d:>7} {d:>7} {d:>7} {s}\n", .{
                counts.lines,
                counts.words,
                counts.bytes,
                path,
            }) catch std.process.exit(1);
            out.flush() catch std.process.exit(1);
        },
    }
}

test "no arguments is a usage error" {
    try std.testing.expectEqual(std.meta.Tag(Command).usage, tagOf(parse(&.{})));
}

test "no arguments explains itself" {
    const command = parse(&.{});
    try std.testing.expectEqualStrings("missing FILE", command.usage);
}

test "--help and -h ask for help" {
    try std.testing.expectEqual(std.meta.Tag(Command).help, tagOf(parse(&.{"--help"})));
    try std.testing.expectEqual(std.meta.Tag(Command).help, tagOf(parse(&.{"-h"})));
}

test "an unknown flag is a usage error" {
    try std.testing.expectEqual(std.meta.Tag(Command).usage, tagOf(parse(&.{"--bogus"})));
    try std.testing.expectEqual(std.meta.Tag(Command).usage, tagOf(parse(&.{"-x"})));
}

test "a single path is counted" {
    const command = parse(&.{"notes.txt"});
    try std.testing.expectEqual(std.meta.Tag(Command).count, tagOf(command));
    try std.testing.expectEqualStrings("notes.txt", command.count);
}

test "a second path is a usage error" {
    try std.testing.expectEqual(std.meta.Tag(Command).usage, tagOf(parse(&.{ "a.txt", "b.txt" })));
}

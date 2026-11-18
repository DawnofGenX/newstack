//! `{{ title }}` — a fixed-width bitset calculator.
//!
//! Thin layer: this file owns argv, exit codes and printing. Every set
//! operation lives in `bitset.zig`.

const std = @import("std");
const Io = std.Io;
const bitset = @import("bitset.zig");

pub const program_name = "{{ package_name }}";

pub const usage_text =
    \\Usage: {s} --len N [--set INDEX,...] [QUERY]
    \\
    \\Build a bitset of N bits, set the given 0-based indexes, and answer one
    \\query about it.
    \\
    \\Options:
    \\  --len N          number of bits (required)
    \\  --set INDEX,...  comma-separated indexes to set
    \\  --has N          report whether bit N is set
    \\  --rank N         report how many set bits lie below N
    \\  --select N       report the index of the N-th set bit
    \\  --count          report the number of set bits
    \\  -h, --help       show this help and exit
    \\
    \\Exit codes:
    \\  0  success (or --help)
    \\  1  an index was out of range or could not be parsed
    \\  2  usage error (unknown flag, missing --len, extra argument)
    \\
;

pub const Config = struct {
    len: usize,
    set: []const u8,
    has: ?usize = null,
    rank: ?usize = null,
    select: ?usize = null,
    count: bool = false,
};

pub const Command = union(enum) {
    help,
    usage: []const u8,
    run: Config,
};

fn parseSize(text: []const u8) ?usize {
    return std.fmt.parseInt(usize, text, 10) catch null;
}

/// Decides what to do from the arguments after the program name. Pure: no
/// printing and no exits, so the tests drive it directly.
pub fn parse(args: []const []const u8) Command {
    var len: ?usize = null;
    var set: []const u8 = "";
    var has: ?usize = null;
    var rank: ?usize = null;
    var select: ?usize = null;
    var count = false;

    var index: usize = 0;
    while (index < args.len) : (index += 1) {
        const arg = args[index];
        if (std.mem.eql(u8, arg, "--help") or std.mem.eql(u8, arg, "-h")) return .help;
        if (std.mem.eql(u8, arg, "--count")) {
            count = true;
            continue;
        }
        const takes_value = std.mem.eql(u8, arg, "--len")
            or std.mem.eql(u8, arg, "--set")
            or std.mem.eql(u8, arg, "--has")
            or std.mem.eql(u8, arg, "--rank")
            or std.mem.eql(u8, arg, "--select");
        if (!takes_value) return .{ .usage = "unknown option or argument" };
        if (index + 1 >= args.len) return .{ .usage = "option needs a value" };
        index += 1;
        const value = args[index];
        if (std.mem.eql(u8, arg, "--len")) {
            len = parseSize(value) orelse return .{ .usage = "--len needs a number" };
        } else if (std.mem.eql(u8, arg, "--set")) {
            set = value;
        } else if (std.mem.eql(u8, arg, "--has")) {
            has = parseSize(value) orelse return .{ .usage = "--has needs a number" };
        } else if (std.mem.eql(u8, arg, "--rank")) {
            rank = parseSize(value) orelse return .{ .usage = "--rank needs a number" };
        } else {
            select = parseSize(value) orelse return .{ .usage = "--select needs a number" };
        }
    }

    const width = len orelse return .{ .usage = "missing --len" };
    if (width == 0) return .{ .usage = "--len must be positive" };
    return .{ .run = .{ .len = width, .set = set, .has = has, .rank = rank, .select = select, .count = count } };
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
            try out.print(usage_text, .{program_name});
            try out.flush();
            return;
        },
        .usage => |reason| {
            err.print("{s}: {s}\n\n", .{ program_name, reason }) catch {};
            err.print(usage_text, .{program_name}) catch {};
            err.flush() catch {};
            std.process.exit(2);
        },
        .run => |run| run,
    };

    const word_count = (config.len + 63) / 64;
    const words = arena.alloc(u64, word_count) catch std.process.exit(1);
    var set = bitset.Bitset.init(words, config.len);

    var iter = std.mem.splitScalar(u8, config.set, ',');
    while (iter.next()) |piece| {
        const trimmed = std.mem.trim(u8, piece, " \t");
        if (trimmed.len == 0) continue;
        const position = parseSize(trimmed) orelse {
            err.print("{s}: not an index: {s}\n", .{ program_name, trimmed }) catch {};
            err.flush() catch {};
            std.process.exit(1);
        };
        if (!set.set(position)) {
            err.print("{s}: index {d} is outside 0..{d}\n", .{ program_name, position, config.len }) catch {};
            err.flush() catch {};
            std.process.exit(1);
        }
    }

    var answered = false;
    if (config.count) {
        out.print("count={d}\n", .{set.count()}) catch std.process.exit(1);
        answered = true;
    }
    if (config.has) |position| {
        out.print("has[{d}]={s}\n", .{ position, if (set.isSet(position)) "true" else "false" }) catch std.process.exit(1);
        answered = true;
    }
    if (config.rank) |position| {
        out.print("rank[{d}]={d}\n", .{ position, set.rank(position) }) catch std.process.exit(1);
        answered = true;
    }
    if (config.select) |order| {
        if (set.select(order)) |position| {
            out.print("select[{d}]={d}\n", .{ order, position }) catch std.process.exit(1);
        } else {
            out.print("select[{d}]=none\n", .{order}) catch std.process.exit(1);
        }
        answered = true;
    }
    if (!answered) {
        out.print("len={d} count={d}\n", .{ config.len, set.count() }) catch std.process.exit(1);
    }
    out.flush() catch std.process.exit(1);
}

test "missing --len is a usage error" {
    try std.testing.expectEqual(std.meta.Tag(Command).usage, tagOf(parse(&.{})));
    const command = parse(&.{});
    try std.testing.expectEqualStrings("missing --len", command.usage);
}

test "--help and -h ask for help" {
    try std.testing.expectEqual(std.meta.Tag(Command).help, tagOf(parse(&.{"--help"})));
    try std.testing.expectEqual(std.meta.Tag(Command).help, tagOf(parse(&.{"-h"})));
}

test "an unknown flag is a usage error" {
    try std.testing.expectEqual(std.meta.Tag(Command).usage, tagOf(parse(&.{ "--len", "8", "--bogus" })));
}

test "a flag without a value is a usage error" {
    try std.testing.expectEqual(std.meta.Tag(Command).usage, tagOf(parse(&.{"--len"})));
}

test "a non-numeric length is a usage error" {
    try std.testing.expectEqual(std.meta.Tag(Command).usage, tagOf(parse(&.{ "--len", "many" })));
}

test "a zero length is refused" {
    try std.testing.expectEqual(std.meta.Tag(Command).usage, tagOf(parse(&.{ "--len", "0" })));
}

test "a full command carries its queries" {
    const command = parse(&.{ "--len", "16", "--set", "1,2", "--rank", "3", "--count" });
    try std.testing.expectEqual(std.meta.Tag(Command).run, tagOf(command));
    try std.testing.expectEqual(@as(usize, 16), command.run.len);
    try std.testing.expectEqualStrings("1,2", command.run.set);
    try std.testing.expectEqual(@as(?usize, 3), command.run.rank);
    try std.testing.expect(command.run.count);
}

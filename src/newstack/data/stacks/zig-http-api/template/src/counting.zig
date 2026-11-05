//! Pure counting: no I/O, no allocations, no globals. `main.zig` reads the
//! bytes; everything that decides the answer lives here so it can be tested.

const std = @import("std");

pub const Counts = struct {
    lines: usize,
    words: usize,
    bytes: usize,
};

/// Count newlines, whitespace-separated words, and raw bytes.
///
/// Lines follow `wc -l`: the number of `\n` bytes, so a final line without a
/// newline terminator is not counted. Words are maximal runs of non-whitespace.
pub fn count(data: []const u8) Counts {
    var counts: Counts = .{ .lines = 0, .words = 0, .bytes = data.len };
    var in_word = false;
    for (data) |byte| {
        if (byte == '\n') counts.lines += 1;
        if (std.ascii.isWhitespace(byte)) {
            in_word = false;
        } else if (!in_word) {
            in_word = true;
            counts.words += 1;
        }
    }
    return counts;
}

test "empty input counts nothing" {
    const counts = count("");
    try std.testing.expectEqual(@as(usize, 0), counts.lines);
    try std.testing.expectEqual(@as(usize, 0), counts.words);
    try std.testing.expectEqual(@as(usize, 0), counts.bytes);
}

test "one line of two words" {
    const counts = count("hello world\n");
    try std.testing.expectEqual(@as(usize, 1), counts.lines);
    try std.testing.expectEqual(@as(usize, 2), counts.words);
    try std.testing.expectEqual(@as(usize, 12), counts.bytes);
}

test "runs of whitespace separate words without adding empty ones" {
    const counts = count("one\n two  three");
    try std.testing.expectEqual(@as(usize, 1), counts.lines);
    try std.testing.expectEqual(@as(usize, 3), counts.words);
    try std.testing.expectEqual(@as(usize, 15), counts.bytes);
}

test "a file with no trailing newline has no counted line" {
    const counts = count("abc");
    try std.testing.expectEqual(@as(usize, 0), counts.lines);
    try std.testing.expectEqual(@as(usize, 1), counts.words);
    try std.testing.expectEqual(@as(usize, 3), counts.bytes);
}

test "blank lines count as lines but not as words" {
    const counts = count("a\n\n\nb\n");
    try std.testing.expectEqual(@as(usize, 4), counts.lines);
    try std.testing.expectEqual(@as(usize, 2), counts.words);
    try std.testing.expectEqual(@as(usize, 6), counts.bytes);
}

test "carriage returns are whitespace, bytes are bytes" {
    const counts = count("a\r\nb\r\n");
    try std.testing.expectEqual(@as(usize, 2), counts.lines);
    try std.testing.expectEqual(@as(usize, 2), counts.words);
    try std.testing.expectEqual(@as(usize, 6), counts.bytes);
}

test "multi-byte characters count as their byte length" {
    const counts = count("h\xc3\xa9llo\n");
    try std.testing.expectEqual(@as(usize, 1), counts.lines);
    try std.testing.expectEqual(@as(usize, 1), counts.words);
    try std.testing.expectEqual(@as(usize, 7), counts.bytes);
}

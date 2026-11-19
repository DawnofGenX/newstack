//! CRC-32 (the IEEE 802.3 / zlib / gzip polynomial) in its bitwise form.
//!
//! Bitwise rather than table-driven on purpose: 32 lines of obvious code beat
//! a 256-entry table for a checksum that runs once per command line.

const std = @import("std");

/// The reflected form of the polynomial 0x04C11DB7.
pub const polynomial: u32 = 0xEDB88320;

/// Folds one byte into a running (already inverted) register.
pub fn update(register: u32, byte: u8) u32 {
    var value = register ^ byte;
    var bit: u5 = 0;
    while (bit < 8) : (bit += 1) {
        value = if (value & 1 == 1) (value >> 1) ^ polynomial else value >> 1;
    }
    return value;
}

/// The CRC-32 of `data`: init 0xFFFFFFFF, reflected, final xor 0xFFFFFFFF.
pub fn hash(data: []const u8) u32 {
    var register: u32 = 0xFFFFFFFF;
    for (data) |byte| register = update(register, byte);
    return register ^ 0xFFFFFFFF;
}

/// Lower-case, zero-padded, eight-digit hexadecimal.
pub fn toHex(buffer: *[8]u8, value: u32) []const u8 {
    return std.fmt.bufPrint(buffer, "{x:0>8}", .{value}) catch unreachable;
}

test "the empty input hashes to zero" {
    try std.testing.expectEqual(@as(u32, 0), hash(""));
}

test "single bytes match the published check values" {
    try std.testing.expectEqual(@as(u32, 0xE8B7BE43), hash("a"));
    try std.testing.expectEqual(@as(u32, 0x352441C2), hash("abc"));
}

test "the standard check vector" {
    try std.testing.expectEqual(@as(u32, 0xCBF43926), hash("123456789"));
}

test "the quick brown fox vector" {
    try std.testing.expectEqual(@as(u32, 0x414FA339), hash("The quick brown fox jumps over the lazy dog"));
}

test "hex output is lower-case and padded" {
    var buffer: [8]u8 = undefined;
    try std.testing.expectEqualStrings("cbf43926", toHex(&buffer, hash("123456789")));
    try std.testing.expectEqualStrings("00000000", toHex(&buffer, hash("")));
}

test "concatenation is not the same as hashing the parts" {
    try std.testing.expect(hash("ab") != hash("a") ^ hash("b"));
}

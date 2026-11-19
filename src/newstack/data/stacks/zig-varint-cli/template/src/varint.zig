//! Pure unsigned LEB128 varint encoding and decoding. No I/O, no allocations.
// stack: zig-varint-cli

const std = @import("std");

pub const VarintError = error{ Overflow, Truncated, Trailing };

/// Encode `value` as unsigned LEB128 into `out`, returning bytes written.
pub fn encodeUleb128(value: u64, out: []u8) usize {
    var v = value;
    var i: usize = 0;
    while (true) {
        var byte: u8 = @intCast(v & 0x7f);
        v >>= 7;
        if (v != 0) byte |= 0x80;
        out[i] = byte;
        i += 1;
        if (v == 0) break;
    }
    return i;
}

/// Decode an unsigned LEB128 value from `data`, returning (value, bytes consumed).
pub fn decodeUleb128(data: []const u8) VarintError!struct { value: u64, len: usize } {
    var result: u64 = 0;
    var shift: u6 = 0;
    var i: usize = 0;
    while (i < data.len) {
        const byte = data[i];
        i += 1;
        if (shift == 63) {
            // only top 1 bit allowed when shift==63
            if (byte & 0x7e != 0) return error.Overflow;
        }
        result |= @as(u64, byte & 0x7f) << shift;
        if (byte & 0x80 == 0) {
            return .{ .value = result, .len = i };
        }
        if (shift == 63) return error.Overflow;
        shift += 7;
        if (i == data.len and (byte & 0x80) != 0) return error.Truncated;
    }
    return error.Truncated;
}

test "encode 0 is single zero byte" {
    var buf: [10]u8 = undefined;
    const n = encodeUleb128(0, &buf);
    try std.testing.expectEqual(@as(usize, 1), n);
    try std.testing.expectEqual(@as(u8, 0), buf[0]);
}

test "encode 127 is single byte" {
    var buf: [10]u8 = undefined;
    const n = encodeUleb128(127, &buf);
    try std.testing.expectEqual(@as(usize, 1), n);
    try std.testing.expectEqual(@as(u8, 127), buf[0]);
}

test "encode 128 uses two bytes" {
    var buf: [10]u8 = undefined;
    const n = encodeUleb128(128, &buf);
    try std.testing.expectEqual(@as(usize, 2), n);
    try std.testing.expectEqual(@as(u8, 0x80), buf[0]);
    try std.testing.expectEqual(@as(u8, 0x01), buf[1]);
}

test "round trip small values" {
    var buf: [10]u8 = undefined;
    var v: u64 = 0;
    while (v < 10000) : (v += 1) {
        const n = encodeUleb128(v, &buf);
        const r = try decodeUleb128(buf[0..n]);
        try std.testing.expectEqual(v, r.value);
        try std.testing.expectEqual(n, r.len);
    }
}

test "round trip powers and max" {
    var buf: [10]u8 = undefined;
    const vals = [_]u64{ 0, 1, 127, 128, 255, 256, 65535, 65536, 1 << 35, 1 << 63, std.math.maxInt(u64) };
    for (vals) |v| {
        const n = encodeUleb128(v, &buf);
        const r = try decodeUleb128(buf[0..n]);
        try std.testing.expectEqual(v, r.value);
    }
}

test "decode rejects truncated" {
    const data = [_]u8{0x80};
    try std.testing.expectError(error.Truncated, decodeUleb128(&data));
}

test "decode rejects overflow" {
    // 10 bytes all 0x80 then 0x01 -> overflow
    const data = [_]u8{ 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x80, 0x01 };
    try std.testing.expectError(error.Overflow, decodeUleb128(&data));
}

test "decode ignores trailing only if exact slice" {
    const data = [_]u8{ 0x05, 0x00 };
    const r = try decodeUleb128(&data);
    try std.testing.expectEqual(@as(u64, 5), r.value);
    try std.testing.expectEqual(@as(usize, 1), r.len);
}
//! Pure bitset operations: no I/O, no globals, no allocation of its own. The
//! caller owns the `[]u64` the set is carved out of, so every operation here is
//! a pure function of its arguments and the tests need no allocator.

const std = @import("std");

pub const Bitset = struct {
    words: []u64,
    len: usize,

    /// Zeroes the caller's words and binds them to `len` bits.
    pub fn init(words: []u64, len: usize) Bitset {
        @memset(words, 0);
        return .{ .words = words, .len = len };
    }

    fn wordIndex(index: usize) usize {
        return index / 64;
    }

    fn bitMask(index: usize) u64 {
        return @as(u64, 1) << @intCast(index % 64);
    }

    pub fn isSet(self: Bitset, index: usize) bool {
        if (index >= self.len) return false;
        return (self.words[wordIndex(index)] & bitMask(index)) != 0;
    }

    /// Returns false when the index is out of range instead of corrupting the
    /// last word with a shift the compiler would have to mask.
    pub fn set(self: *Bitset, index: usize) bool {
        if (index >= self.len) return false;
        self.words[wordIndex(index)] |= bitMask(index);
        return true;
    }

    pub fn unset(self: *Bitset, index: usize) bool {
        if (index >= self.len) return false;
        self.words[wordIndex(index)] &= ~bitMask(index);
        return true;
    }

    /// Number of set bits below `len`, ignoring any spare bits in the last word.
    pub fn count(self: Bitset) usize {
        var total: usize = 0;
        const full = self.len / 64;
        for (self.words[0..full]) |word| total += @popCount(word);
        const rest = self.len % 64;
        if (rest != 0) {
            const mask = (@as(u64, 1) << @intCast(rest)) - 1;
            total += @popCount(self.words[full] & mask);
        }
        return total;
    }

    /// Number of set bits in [0, index): a prefix count, so rank(0) is 0.
    pub fn rank(self: Bitset, index: usize) usize {
        const limit = @min(index, self.len);
        if (limit == 0) return 0;
        var total: usize = 0;
        const full = limit / 64;
        for (self.words[0..full]) |word| total += @popCount(word);
        const rest = limit % 64;
        if (rest != 0) {
            const mask = (@as(u64, 1) << @intCast(rest)) - 1;
            total += @popCount(self.words[full] & mask);
        }
        return total;
    }

    /// Position of the `order`-th set bit (0-based), or null when there are not
    /// that many. `select(rank(i)) == i` for every set bit.
    pub fn select(self: Bitset, order: usize) ?usize {
        var remaining = order;
        for (self.words, 0..) |word, word_index| {
            const bits: usize = @popCount(word);
            if (remaining >= bits) {
                remaining -= bits;
                continue;
            }
            var scan = word;
            var bit: usize = 0;
            while (true) : (bit += 1) {
                if (scan & 1 != 0) {
                    if (remaining == 0) {
                        const position = word_index * 64 + bit;
                        return if (position < self.len) position else null;
                    }
                    remaining -= 1;
                }
                scan >>= 1;
            }
        }
        return null;
    }
};

test "an empty set has nothing set" {
    var words: [1]u64 = undefined;
    const set = Bitset.init(&words, 0);
    try std.testing.expectEqual(@as(usize, 0), set.count());
    try std.testing.expect(!set.isSet(0));
    try std.testing.expectEqual(@as(?usize, null), set.select(0));
}

test "setting and unsetting a bit" {
    var words: [2]u64 = undefined;
    var set = Bitset.init(&words, 100);
    try std.testing.expect(set.set(5));
    try std.testing.expect(set.isSet(5));
    try std.testing.expectEqual(@as(usize, 1), set.count());
    try std.testing.expect(set.unset(5));
    try std.testing.expect(!set.isSet(5));
    try std.testing.expectEqual(@as(usize, 0), set.count());
}

test "an out-of-range index is refused, not masked" {
    var words: [1]u64 = undefined;
    var set = Bitset.init(&words, 10);
    try std.testing.expect(!set.set(10));
    try std.testing.expect(!set.unset(64));
    try std.testing.expect(!set.isSet(999));
    try std.testing.expectEqual(@as(usize, 0), set.count());
}

test "spare bits past len are not counted" {
    var words: [1]u64 = undefined;
    var set = Bitset.init(&words, 3);
    set.words[0] = 0xFFFF;
    try std.testing.expectEqual(@as(usize, 3), set.count());
    try std.testing.expectEqual(@as(usize, 3), set.rank(3));
}

test "rank is a prefix count" {
    var words: [2]u64 = undefined;
    var set = Bitset.init(&words, 128);
    for ([_]usize{ 0, 1, 2, 63, 64, 65, 127 }) |index| _ = set.set(index);
    try std.testing.expectEqual(@as(usize, 0), set.rank(0));
    try std.testing.expectEqual(@as(usize, 1), set.rank(1));
    try std.testing.expectEqual(@as(usize, 3), set.rank(3));
    try std.testing.expectEqual(@as(usize, 4), set.rank(64));
    try std.testing.expectEqual(@as(usize, 5), set.rank(65));
    try std.testing.expectEqual(@as(usize, 7), set.rank(128));
}

test "select finds the n-th set bit" {
    var words: [2]u64 = undefined;
    var set = Bitset.init(&words, 128);
    for ([_]usize{ 3, 70, 71 }) |index| _ = set.set(index);
    try std.testing.expectEqual(@as(?usize, 3), set.select(0));
    try std.testing.expectEqual(@as(?usize, 70), set.select(1));
    try std.testing.expectEqual(@as(?usize, 71), set.select(2));
    try std.testing.expectEqual(@as(?usize, null), set.select(3));
}

test "select and rank are inverse on set bits" {
    var words: [4]u64 = undefined;
    var set = Bitset.init(&words, 200);
    for ([_]usize{ 1, 64, 130, 199 }) |index| _ = set.set(index);
    for (0..4) |order| {
        const position = set.select(order).?;
        try std.testing.expectEqual(order, set.rank(position));
    }
}

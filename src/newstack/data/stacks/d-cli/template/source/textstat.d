/// Counting that matches wc(1): lines are 0x0A bytes, words are maximal runs of
/// non-whitespace bytes, bytes is the payload length.
module textstat;

struct Counts {
    size_t lines;
    size_t words;
    size_t bytes;
}

private bool isSpace(ubyte b) pure nothrow @nogc {
    return b == ' ' || b == '\t' || b == '\n' || b == '\r' || b == 11 || b == 12;
}

Counts count(const(ubyte)[] payload) pure nothrow @nogc {
    size_t lines = 0;
    size_t words = 0;
    bool inWord = false;

    foreach (b; payload) {
        if (b == '\n') lines++;
        if (isSpace(b)) {
            inWord = false;
        } else if (!inWord) {
            inWord = true;
            words++;
        }
    }

    return Counts(lines, words, payload.length);
}

Counts add(Counts a, Counts b) pure nothrow @nogc {
    return Counts(a.lines + b.lines, a.words + b.words, a.bytes + b.bytes);
}

unittest {
    auto plain = count(cast(const(ubyte)[]) "alpha beta\ngamma\n");
    assert(plain.lines == 2);
    assert(plain.words == 3);
    assert(plain.bytes == 17);
}

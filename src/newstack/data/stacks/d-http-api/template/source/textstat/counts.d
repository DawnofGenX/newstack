/// Byte-exact counting, the same rules wc(1) uses.
module textstat.counts;

struct Counts
{
    size_t lines;
    size_t words;
    size_t bytes;
}

/// Counts a UTF-8 string: a line is '\n', a word is a maximal run of non-space
/// characters, and bytes is the raw payload length.
Counts countText(string text)
{
    Counts counts;
    bool inWord = false;

    foreach (char character; text)
    {
        counts.bytes++;
        if (character == '\n')
            counts.lines++;
        if (character == ' ' || character == '\t' || character == '\n' ||
            character == '\r' || character == '\v' || character == '\f')
        {
            inWord = false;
        }
        else if (!inWord)
        {
            counts.words++;
            inWord = true;
        }
    }
    return counts;
}

unittest
{
    assert(countText("").lines == 0);
    assert(countText("hello world\n") == Counts(1, 2, 12));
    assert(countText("one two\nthree\n") == Counts(2, 3, 14));
    assert(countText("\n\nx\n") == Counts(3, 1, 4));
    assert(countText("  \t ") == Counts(0, 0, 4));
    assert(countText("abc") == Counts(0, 1, 3));
    // UTF-8: 12 characters, 14 bytes.
    assert(countText("héllo wörld\n") == Counts(1, 2, 14));
    // An emoji is one code point, four bytes, and never a space.
    assert(countText("🙂\n") == Counts(1, 1, 5));
}

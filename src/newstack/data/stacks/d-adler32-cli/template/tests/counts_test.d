module counts_test;

import harness;
import textstat;

void runCountsTests() {
    auto plain = count(cast(const(ubyte)[]) "alpha beta\ngamma\n");
    Harness.equalInt("two lines", plain.lines, 2);
    Harness.equalInt("three words", plain.words, 3);
    Harness.equalInt("bytes are the payload length", plain.bytes, 17);

    auto noTrailing = count(cast(const(ubyte)[]) "one two three");
    Harness.equalInt("no trailing newline: lines", noTrailing.lines, 0);
    Harness.equalInt("no trailing newline: words", noTrailing.words, 3);

    auto empty = count(cast(const(ubyte)[]) "");
    Harness.equalInt("empty lines", empty.lines, 0);
    Harness.equalInt("empty bytes", empty.bytes, 0);

    auto spaced = count(cast(const(ubyte)[]) "   ");
    Harness.equalInt("whitespace only has no words", spaced.words, 0);

    auto controls = count(cast(const(ubyte)[]) "a\tb\011c\012d\n");
    Harness.equalInt("tab, vtab and form feed separate words", controls.words, 4);

    auto sum = add(plain, noTrailing);
    Harness.equalInt("add sums lines", sum.lines, 2);
    Harness.equalInt("add sums words", sum.words, 6);
}

#include "check.hpp"
#include "textstat/counters.hpp"

int main() {
    {
        const textstat::Counts counts = textstat::count_text("");
        CHECK_EQ(counts.lines, 0U);
        CHECK_EQ(counts.words, 0U);
        CHECK_EQ(counts.bytes, 0U);
    }
    {
        const textstat::Counts counts = textstat::count_text("alpha beta\n");
        CHECK_EQ(counts.lines, 1U);
        CHECK_EQ(counts.words, 2U);
        CHECK_EQ(counts.bytes, 11U);
    }
    {
        const textstat::Counts counts = textstat::count_text("one\ttwo  three\r\nfour\n");
        CHECK_EQ(counts.lines, 2U);
        CHECK_EQ(counts.words, 4U);
        CHECK_EQ(counts.bytes, 21U);
    }
    {
        // No trailing newline: the last partial line is still a word, not a line.
        const textstat::Counts counts = textstat::count_text("no newline here");
        CHECK_EQ(counts.lines, 0U);
        CHECK_EQ(counts.words, 3U);
        CHECK_EQ(counts.bytes, 15U);
    }
    {
        textstat::Counts total;
        total += textstat::count_text("a b\n");
        total += textstat::count_text("c\n");
        CHECK_EQ(total.lines, 2U);
        CHECK_EQ(total.words, 3U);
        CHECK_EQ(total.bytes, 6U);
    }
    return testing::report("counters");
}

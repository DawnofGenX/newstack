#include "check.h"

#include "textstat/counters.h"

int run_counters_tests(void) {
    int failures = 0;

    struct textstat_counts counts = textstat_count("", 0);
    CHECK_SIZE(counts.lines, 0);
    CHECK_SIZE(counts.words, 0);
    CHECK_SIZE(counts.bytes, 0);

    const char *hello = "hello world\n";
    counts = textstat_count(hello, strlen(hello));
    CHECK_SIZE(counts.lines, 1);
    CHECK_SIZE(counts.words, 2);
    CHECK_SIZE(counts.bytes, 12);

    const char *two_lines = "one two\nthree\n";
    counts = textstat_count(two_lines, strlen(two_lines));
    CHECK_SIZE(counts.lines, 2);
    CHECK_SIZE(counts.words, 3);
    CHECK_SIZE(counts.bytes, 14);

    /* Blank lines count as lines but never as words. */
    const char *blanks = "\n\nx\n";
    counts = textstat_count(blanks, strlen(blanks));
    CHECK_SIZE(counts.lines, 3);
    CHECK_SIZE(counts.words, 1);
    CHECK_SIZE(counts.bytes, 4);

    /* Whitespace with no newline: bytes only. */
    const char *spaces = "  \t ";
    counts = textstat_count(spaces, strlen(spaces));
    CHECK_SIZE(counts.lines, 0);
    CHECK_SIZE(counts.words, 0);
    CHECK_SIZE(counts.bytes, 4);

    /* A final line without a newline is still a word, and multibyte UTF-8
     * counts as bytes, not characters. */
    const char *no_newline = "abc";
    counts = textstat_count(no_newline, strlen(no_newline));
    CHECK_SIZE(counts.lines, 0);
    CHECK_SIZE(counts.words, 1);
    CHECK_SIZE(counts.bytes, 3);

    const char *utf8 = "h\xc3\xa9llo w\xc3\xb6rld\n";
    counts = textstat_count(utf8, strlen(utf8));
    CHECK_SIZE(counts.lines, 1);
    CHECK_SIZE(counts.words, 2);
    CHECK_SIZE(counts.bytes, 14);

    const struct textstat_counts first = textstat_count("a b\n", 4);
    const struct textstat_counts second = textstat_count("c\n", 2);
    const struct textstat_counts total = textstat_counts_add(first, second);
    CHECK_SIZE(total.lines, 2);
    CHECK_SIZE(total.words, 3);
    CHECK_SIZE(total.bytes, 6);

    return failures;
}

#include "check.hpp"

namespace {

using textstat::check::counts_are;

}  // namespace

void counts_tests() {
    counts_are("empty input", "", 0, 0, 0);
    counts_are("one line", "hello world\n", 1, 2, 12);
    counts_are("two lines", "a b\nc\n", 2, 3, 6);
    counts_are("blank lines", "\n\nx\n", 3, 1, 4);
    counts_are("spaces only", "  \t ", 0, 0, 4);
    counts_are("no trailing newline", "abc", 0, 1, 3);
    counts_are("utf-8 payload", "h\xc3\xa9llo w\xc3\xb6rld\n", 1, 2, 14);
    counts_are("emoji", "\xf0\x9f\x99\x82\n", 1, 1, 5);
}

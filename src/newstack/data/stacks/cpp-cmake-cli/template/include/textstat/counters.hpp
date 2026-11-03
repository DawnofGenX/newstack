#pragma once

#include <cstddef>
#include <string_view>

namespace textstat {

/// Line, word and byte totals for one input.
///
/// Counting follows `wc`: a line is a `'\n'`, a word is a maximal run of
/// non-whitespace bytes, and bytes are the raw payload length.
struct Counts {
    std::size_t lines = 0;
    std::size_t words = 0;
    std::size_t bytes = 0;

    Counts &operator+=(const Counts &other) noexcept {
        lines += other.lines;
        words += other.words;
        bytes += other.bytes;
        return *this;
    }
};

/// Count lines, words and bytes in `text`.
Counts count_text(std::string_view text) noexcept;

} // namespace textstat

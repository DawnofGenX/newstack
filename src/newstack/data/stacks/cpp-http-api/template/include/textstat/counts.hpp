#ifndef TEXTSTAT_COUNTS_HPP
#define TEXTSTAT_COUNTS_HPP

#include <cstddef>
#include <string_view>

namespace textstat {

// What wc reports: a line is one '\n', a word is a maximal run of non-space
// bytes, and bytes are the raw UTF-8 length.
struct Counts {
    std::size_t lines = 0;
    std::size_t words = 0;
    std::size_t bytes = 0;
};

Counts count(std::string_view data);

}  // namespace textstat

#endif

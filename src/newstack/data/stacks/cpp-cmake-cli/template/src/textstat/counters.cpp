#include "textstat/counters.hpp"

namespace textstat {
namespace {

bool is_space(unsigned char byte) noexcept {
    return byte == ' ' || byte == '\n' || byte == '\t' || byte == '\r' || byte == '\v' ||
           byte == '\f';
}

} // namespace

Counts count_text(std::string_view text) noexcept {
    Counts counts;
    counts.bytes = text.size();

    bool in_word = false;
    for (const char raw : text) {
        const auto byte = static_cast<unsigned char>(raw);
        if (byte == '\n') {
            ++counts.lines;
        }
        if (is_space(byte)) {
            in_word = false;
        } else if (!in_word) {
            in_word = true;
            ++counts.words;
        }
    }
    return counts;
}

} // namespace textstat

#include "textstat/counts.hpp"

namespace textstat {
namespace {

bool is_space(unsigned char value) {
    return value == ' ' || value == '\t' || value == '\n' || value == '\r' ||
           value == 0x0b || value == 0x0c;
}

}  // namespace

Counts count(std::string_view data) {
    Counts totals;
    bool in_word = false;
    for (unsigned char byte : data) {
        totals.bytes += 1;
        if (byte == '\n') {
            totals.lines += 1;
        }
        if (is_space(byte)) {
            in_word = false;
        } else if (!in_word) {
            in_word = true;
            totals.words += 1;
        }
    }
    return totals;
}

}  // namespace textstat

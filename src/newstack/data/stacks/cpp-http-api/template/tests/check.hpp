#ifndef TEXTSTAT_CHECK_HPP
#define TEXTSTAT_CHECK_HPP

#include <iostream>
#include <string>
#include <string_view>

#include "textstat/contract.hpp"
#include "textstat/counts.hpp"
#include "textstat/json.hpp"

namespace textstat {
namespace check {

inline int &failures() {
    static int count = 0;
    return count;
}

inline int &passes() {
    static int count = 0;
    return count;
}

inline void report(std::string_view name, bool ok) {
    if (ok) {
        passes() += 1;
        return;
    }
    failures() += 1;
    std::cout << "FAIL " << name << '\n';
}

inline void equal(std::string_view name, long long got, long long want) {
    if (got == want) {
        report(name, true);
        return;
    }
    failures() += 1;
    std::cout << "FAIL " << name << " (got " << got << ", want " << want << ")\n";
}

inline void equal(std::string_view name, std::string_view got, std::string_view want) {
    if (got == want) {
        report(name, true);
        return;
    }
    failures() += 1;
    std::cout << "FAIL " << name << " (got \"" << got << "\", want \"" << want << "\")\n";
}

inline void counts_are(std::string_view name, std::string_view text, long long lines,
                       long long words, long long bytes) {
    const Counts totals = count(text);
    equal(name, static_cast<long long>(totals.lines), lines);
    equal(name, static_cast<long long>(totals.words), words);
    equal(name, static_cast<long long>(totals.bytes), bytes);
}

inline int summary() {
    std::cout << "checks: " << (passes() + failures()) << ", passed: " << passes()
              << ", failed: " << failures() << '\n';
    return failures() == 0 ? 0 : 1;
}

}  // namespace check
}  // namespace textstat

#endif

#pragma once

// A deliberately tiny assertion helper: no download, no framework, so the
// template builds and tests offline right after `cmake -S . -B build`.

#include <cstdio>
#include <string>
#include <string_view>

namespace testing {

inline int failures = 0;

inline void check(bool condition, std::string_view expression, const char *file, int line) {
    if (!condition) {
        ++failures;
        std::fprintf(stderr, "%s:%d: check failed: %s\n", file, line,
                     std::string(expression).c_str());
    }
}

inline int report(std::string_view name) {
    if (failures == 0) {
        std::printf("ok - %s\n", std::string(name).c_str());
        return 0;
    }
    std::printf("not ok - %s (%d failure(s))\n", std::string(name).c_str(), failures);
    return 1;
}

} // namespace testing

#define CHECK(condition) ::testing::check((condition), #condition, __FILE__, __LINE__)
#define CHECK_EQ(actual, expected)                                                                 \
    ::testing::check((actual) == (expected), #actual " == " #expected, __FILE__, __LINE__)

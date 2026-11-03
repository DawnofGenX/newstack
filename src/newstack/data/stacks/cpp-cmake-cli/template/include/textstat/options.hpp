#pragma once

#include <string>
#include <string_view>
#include <vector>

namespace textstat {

inline constexpr std::string_view kVersion = "0.1.0";

/// What to print. `All` is lines + words + bytes, like a bare `wc`.
enum class Mode { All, Lines, Words, Bytes };

struct Options {
    Mode mode = Mode::All;
    std::vector<std::string> files;
};

enum class ParseStatus { Ok, Help, Version, Error };

struct ParseResult {
    ParseStatus status = ParseStatus::Ok;
    Options options;
    std::string error; ///< non-empty only when `status == ParseStatus::Error`
};

/// Parse `argv[1..argc)`. Never touches the filesystem and never exits.
ParseResult parse_args(int argc, const char *const *argv);

/// The help text, starting with a `usage:` line derived from `program`.
std::string usage(std::string_view program);

} // namespace textstat

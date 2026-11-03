#include "textstat/options.hpp"

#include <array>
#include <string>

namespace textstat {
namespace {

struct Flag {
    std::string_view spelling;
    Mode mode;
};

constexpr std::array<Flag, 6> kModeFlags{{
    {"-l", Mode::Lines},
    {"--lines", Mode::Lines},
    {"-w", Mode::Words},
    {"--words", Mode::Words},
    {"-c", Mode::Bytes},
    {"--bytes", Mode::Bytes},
}};

} // namespace

ParseResult parse_args(int argc, const char *const *argv) {
    ParseResult result;
    bool mode_chosen = false;
    bool only_files = false;

    for (int index = 1; index < argc; ++index) {
        const std::string arg = argv[index];

        if (only_files || arg.empty() || arg == "-") {
            result.options.files.push_back(arg);
            continue;
        }
        if (arg == "--") {
            only_files = true;
            continue;
        }
        if (arg == "-h" || arg == "--help") {
            result.status = ParseStatus::Help;
            return result;
        }
        if (arg == "-V" || arg == "--version") {
            result.status = ParseStatus::Version;
            return result;
        }

        bool matched = false;
        for (const Flag &flag : kModeFlags) {
            if (arg != flag.spelling) {
                continue;
            }
            if (mode_chosen && result.options.mode != flag.mode) {
                result.status = ParseStatus::Error;
                result.error = "choose one of -l, -w, -c: '" + arg + "' conflicts with an earlier mode";
                return result;
            }
            result.options.mode = flag.mode;
            mode_chosen = true;
            matched = true;
            break;
        }
        if (matched) {
            continue;
        }
        if (arg.front() == '-') {
            result.status = ParseStatus::Error;
            result.error = "unknown option '" + arg + "'";
            return result;
        }
        result.options.files.push_back(arg);
    }

    return result;
}

std::string usage(std::string_view program) {
    const std::string name(program);
    return "usage: " + name + " [-l | -w | -c] [--] [FILE ...]\n"
           "\n"
           "Count lines, words and bytes in each FILE, or in standard input\n"
           "when no FILE is given. With more than one FILE a total is printed.\n"
           "\n"
           "  -l, --lines     print the line count only\n"
           "  -w, --words     print the word count only\n"
           "  -c, --bytes     print the byte count only\n"
           "  -h, --help      show this help and exit\n"
           "  -V, --version   show the version and exit\n";
}

} // namespace textstat

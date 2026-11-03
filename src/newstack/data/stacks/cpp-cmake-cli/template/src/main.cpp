#include "textstat/counters.hpp"
#include "textstat/options.hpp"

#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <iterator>
#include <string>

namespace {

std::string read_all(std::istream &stream) {
    return std::string(std::istreambuf_iterator<char>(stream), std::istreambuf_iterator<char>());
}

std::string program_name(const char *argv0) {
    if (argv0 == nullptr || *argv0 == '\0') {
        return "counter";
    }
    return std::filesystem::path(argv0).filename().string();
}

void print_counts(const textstat::Counts &counts, textstat::Mode mode,
                  const std::string &label) {
    const bool all = mode == textstat::Mode::All;
    if (all || mode == textstat::Mode::Lines) {
        std::cout << std::setw(8) << counts.lines;
    }
    if (all || mode == textstat::Mode::Words) {
        std::cout << std::setw(8) << counts.words;
    }
    if (all || mode == textstat::Mode::Bytes) {
        std::cout << std::setw(8) << counts.bytes;
    }
    if (!label.empty()) {
        std::cout << ' ' << label;
    }
    std::cout << '\n';
}

} // namespace

int main(int argc, char **argv) {
    const std::string program = program_name(argc > 0 ? argv[0] : nullptr);
    const textstat::ParseResult parsed = textstat::parse_args(argc, argv);

    switch (parsed.status) {
    case textstat::ParseStatus::Help:
        std::cout << textstat::usage(program);
        return 0;
    case textstat::ParseStatus::Version:
        std::cout << textstat::kVersion << '\n';
        return 0;
    case textstat::ParseStatus::Error:
        std::cerr << "error: " << parsed.error << "\n\n" << textstat::usage(program);
        return 2;
    case textstat::ParseStatus::Ok:
        break;
    }

    const textstat::Mode mode = parsed.options.mode;
    const auto &files = parsed.options.files;

    if (files.empty()) {
        print_counts(textstat::count_text(read_all(std::cin)), mode, "");
        return 0;
    }

    textstat::Counts total;
    bool failed = false;
    for (const std::string &path : files) {
        std::ifstream input(path, std::ios::binary);
        if (!input) {
            std::cerr << "error: cannot open '" << path << "'\n";
            failed = true;
            continue;
        }
        const textstat::Counts counts = textstat::count_text(read_all(input));
        total += counts;
        print_counts(counts, mode, path);
    }

    if (files.size() > 1) {
        print_counts(total, mode, "total");
    }
    return failed ? 1 : 0;
}

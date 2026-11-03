#include "check.hpp"
#include "textstat/options.hpp"

#include <string>
#include <vector>

namespace {

textstat::ParseResult parse(std::vector<std::string> words) {
    std::vector<const char *> argv;
    argv.reserve(words.size() + 1);
    argv.push_back("counter");
    for (const std::string &word : words) {
        argv.push_back(word.c_str());
    }
    return textstat::parse_args(static_cast<int>(argv.size()), argv.data());
}

} // namespace

int main() {
    {
        const textstat::ParseResult result = parse({});
        CHECK(result.status == textstat::ParseStatus::Ok);
        CHECK(result.options.mode == textstat::Mode::All);
        CHECK(result.options.files.empty());
    }
    {
        const textstat::ParseResult result = parse({"-l"});
        CHECK(result.status == textstat::ParseStatus::Ok);
        CHECK(result.options.mode == textstat::Mode::Lines);
    }
    {
        const textstat::ParseResult result = parse({"--help"});
        CHECK(result.status == textstat::ParseStatus::Help);
    }
    {
        const textstat::ParseResult result = parse({"--nope"});
        CHECK(result.status == textstat::ParseStatus::Error);
        CHECK_EQ(result.error.find("unknown option"), 0U);
    }
    {
        const textstat::ParseResult result = parse({"-l", "-w"});
        CHECK(result.status == textstat::ParseStatus::Error);
        CHECK_EQ(result.error.find("choose one of"), 0U);
    }
    {
        const textstat::ParseResult result = parse({"-w", "--", "-l", "notes.txt"});
        CHECK(result.status == textstat::ParseStatus::Ok);
        CHECK(result.options.mode == textstat::Mode::Words);
        CHECK_EQ(result.options.files.size(), 2U);
        CHECK_EQ(result.options.files[0], "-l");
        CHECK_EQ(result.options.files[1], "notes.txt");
    }
    {
        const std::string text = textstat::usage("counter");
        CHECK_EQ(text.rfind("usage: counter", 0), 0U);
        CHECK(text.find("--version") != std::string::npos);
    }
    return testing::report("options");
}

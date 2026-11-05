#include "check.hpp"

namespace {

using textstat::TextField;
using textstat::TextKind;
using textstat::check::equal;
using textstat::check::report;
using textstat::read_text;

void kind_is(std::string_view name, std::string_view body, TextKind kind) {
    report(name, read_text(body).kind == kind);
}

}  // namespace

void json_tests() {
    const TextField plain = read_text(R"({"text":"a b\nc\n"})");
    report("a string member is read", plain.kind == TextKind::text);
    equal("escapes are decoded", plain.text, "a b\nc\n");

    equal("utf-8 escapes are decoded", read_text(R"({"text":"h\u00e9llo"})").text,
          "h\xc3\xa9llo");

    const TextField emoji = read_text(R"({"text":"\ud83d\ude42"})");
    report("surrogate pairs are read", emoji.kind == TextKind::text);
    equal("surrogate pair decodes to four bytes", emoji.text, "\xf0\x9f\x99\x82");

    kind_is("a number is not a string", R"({"text":42})", TextKind::missing);
    kind_is("null is not a string", R"({"text":null})", TextKind::missing);
    kind_is("an object is not a string", R"({"text":{"a":1}})", TextKind::missing);
    kind_is("a missing member is missing", R"({"body":"x"})", TextKind::missing);
    kind_is("an empty object is missing", R"({})", TextKind::missing);
    kind_is("a bare word is invalid", "nope", TextKind::invalid);
    kind_is("an array is invalid", R"(["text"])", TextKind::invalid);
    kind_is("trailing data is invalid", R"({"text":"a"} trailing)", TextKind::invalid);
    kind_is("an unterminated string is invalid", R"({"text":"a)", TextKind::invalid);

    const TextField extra = read_text(R"({"n":1,"text":"x","f":true,"o":{"k":[1,2]}})");
    report("other members are skipped", extra.kind == TextKind::text);
    equal("the text member is found among others", extra.text, "x");
}

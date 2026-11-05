#ifndef TEXTSTAT_JSON_HPP
#define TEXTSTAT_JSON_HPP

#include <string>
#include <string_view>

namespace textstat {

// The three states a POST body can be in, from the contract's point of view.
// A JSON body we cannot parse is `invalid`; a body we parse but that has no
// string `text` member is `missing`, and a JSON number or object under `text`
// counts as missing too — only a JSON string is counted.
enum class TextKind { invalid, missing, text };

struct TextField {
    TextKind kind = TextKind::invalid;
    std::string text;
};

TextField read_text(std::string_view body);

}  // namespace textstat

#endif

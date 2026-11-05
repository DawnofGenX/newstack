#include "textstat/json.hpp"

#include <cstdint>
#include <utility>

namespace textstat {
namespace {

// A reader over one JSON document that returns the kind of the top-level
// `text` member. It validates the whole document, so trailing garbage is
// rejected rather than silently ignored.
class Reader {
  public:
    explicit Reader(std::string_view text) : text_(text) {}

    bool parse_object(std::string &text, bool &found, bool &is_string) {
        skip_space();
        if (!take('{')) {
            return false;
        }
        skip_space();
        if (peek() == '}') {
            ++index_;
            return finish();
        }
        for (;;) {
            skip_space();
            std::string key;
            if (!parse_string(key)) {
                return false;
            }
            skip_space();
            if (!take(':')) {
                return false;
            }
            skip_space();
            if (key == "text") {
                found = true;
                if (peek() == '"') {
                    if (!parse_string(text)) {
                        return false;
                    }
                    is_string = true;
                } else if (!skip_value()) {
                    return false;
                }
            } else if (!skip_value()) {
                return false;
            }
            skip_space();
            if (take(',')) {
                continue;
            }
            if (take('}')) {
                return finish();
            }
            return false;
        }
    }

  private:
    char peek() const { return index_ < text_.size() ? text_[index_] : '\0'; }

    bool take(char wanted) {
        if (peek() != wanted) {
            return false;
        }
        ++index_;
        return true;
    }

    bool finish() {
        skip_space();
        return index_ == text_.size();
    }

    void skip_space() {
        while (index_ < text_.size()) {
            char value = text_[index_];
            if (value != ' ' && value != '\t' && value != '\n' && value != '\r') {
                break;
            }
            ++index_;
        }
    }

    bool parse_string(std::string &out) {
        if (!take('"')) {
            return false;
        }
        out.clear();
        while (index_ < text_.size()) {
            char value = text_[index_++];
            if (value == '"') {
                return true;
            }
            if (value != '\\') {
                out.push_back(value);
                continue;
            }
            if (index_ >= text_.size()) {
                return false;
            }
            char escape = text_[index_++];
            switch (escape) {
                case '"': out.push_back('"'); break;
                case '\\': out.push_back('\\'); break;
                case '/': out.push_back('/'); break;
                case 'b': out.push_back('\b'); break;
                case 'f': out.push_back('\f'); break;
                case 'n': out.push_back('\n'); break;
                case 'r': out.push_back('\r'); break;
                case 't': out.push_back('\t'); break;
                case 'u': {
                    std::uint32_t code = 0;
                    if (!read_hex4(code)) {
                        return false;
                    }
                    if (code >= 0xd800 && code <= 0xdbff && index_ + 1 < text_.size() &&
                        text_[index_] == '\\' && text_[index_ + 1] == 'u') {
                        index_ += 2;
                        std::uint32_t low = 0;
                        if (!read_hex4(low)) {
                            return false;
                        }
                        code = 0x10000u + ((code - 0xd800u) << 10) + (low - 0xdc00u);
                    }
                    append_utf8(out, code);
                    break;
                }
                default:
                    return false;
            }
        }
        return false;
    }

    bool read_hex4(std::uint32_t &code) {
        code = 0;
        for (int digit = 0; digit < 4; ++digit) {
            if (index_ >= text_.size()) {
                return false;
            }
            char value = text_[index_++];
            code <<= 4;
            if (value >= '0' && value <= '9') {
                code |= static_cast<std::uint32_t>(value - '0');
            } else if (value >= 'a' && value <= 'f') {
                code |= static_cast<std::uint32_t>(value - 'a' + 10);
            } else if (value >= 'A' && value <= 'F') {
                code |= static_cast<std::uint32_t>(value - 'A' + 10);
            } else {
                return false;
            }
        }
        return true;
    }

    static void append_utf8(std::string &out, std::uint32_t code) {
        if (code < 0x80) {
            out.push_back(static_cast<char>(code));
        } else if (code < 0x800) {
            out.push_back(static_cast<char>(0xc0 | (code >> 6)));
            out.push_back(static_cast<char>(0x80 | (code & 0x3f)));
        } else if (code < 0x10000) {
            out.push_back(static_cast<char>(0xe0 | (code >> 12)));
            out.push_back(static_cast<char>(0x80 | ((code >> 6) & 0x3f)));
            out.push_back(static_cast<char>(0x80 | (code & 0x3f)));
        } else {
            out.push_back(static_cast<char>(0xf0 | (code >> 18)));
            out.push_back(static_cast<char>(0x80 | ((code >> 12) & 0x3f)));
            out.push_back(static_cast<char>(0x80 | ((code >> 6) & 0x3f)));
            out.push_back(static_cast<char>(0x80 | (code & 0x3f)));
        }
    }

    bool skip_number() {
        std::size_t start = index_;
        if (peek() == '-') {
            ++index_;
        }
        while (index_ < text_.size() && text_[index_] >= '0' && text_[index_] <= '9') {
            ++index_;
        }
        if (index_ == start) {
            return false;
        }
        if (peek() == '.') {
            ++index_;
            while (index_ < text_.size() && text_[index_] >= '0' && text_[index_] <= '9') {
                ++index_;
            }
        }
        if (peek() == 'e' || peek() == 'E') {
            ++index_;
            if (peek() == '+' || peek() == '-') {
                ++index_;
            }
            while (index_ < text_.size() && text_[index_] >= '0' && text_[index_] <= '9') {
                ++index_;
            }
        }
        return true;
    }

    bool skip_literal(std::string_view literal) {
        if (text_.substr(index_, literal.size()) != literal) {
            return false;
        }
        index_ += literal.size();
        return true;
    }

    bool skip_value() {
        skip_space();
        char value = peek();
        if (value == '"') {
            std::string ignored;
            return parse_string(ignored);
        }
        if (value == '{') {
            ++index_;
            skip_space();
            if (take('}')) {
                return true;
            }
            for (;;) {
                skip_space();
                std::string key;
                if (!parse_string(key)) {
                    return false;
                }
                skip_space();
                if (!take(':') || !skip_value()) {
                    return false;
                }
                skip_space();
                if (take(',')) {
                    continue;
                }
                return take('}');
            }
        }
        if (value == '[') {
            ++index_;
            skip_space();
            if (take(']')) {
                return true;
            }
            for (;;) {
                if (!skip_value()) {
                    return false;
                }
                skip_space();
                if (take(',')) {
                    continue;
                }
                return take(']');
            }
        }
        if (value == 't') {
            return skip_literal("true");
        }
        if (value == 'f') {
            return skip_literal("false");
        }
        if (value == 'n') {
            return skip_literal("null");
        }
        return skip_number();
    }

    std::string_view text_;
    std::size_t index_ = 0;
};

}  // namespace

TextField read_text(std::string_view body) {
    Reader reader(body);
    std::string text;
    bool found = false;
    bool is_string = false;
    if (!reader.parse_object(text, found, is_string)) {
        return {};
    }
    if (!found || !is_string) {
        return {TextKind::missing, {}};
    }
    return {TextKind::text, std::move(text)};
}

}  // namespace textstat

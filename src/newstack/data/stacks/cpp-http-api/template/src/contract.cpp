#include "textstat/contract.hpp"

#include <cstdio>
#include <optional>

#include "textstat/counts.hpp"
#include "textstat/json.hpp"

namespace textstat {
namespace {

std::string quote(std::string_view value) {
    std::string out;
    out.push_back('"');
    for (char raw : value) {
        unsigned char byte = static_cast<unsigned char>(raw);
        switch (byte) {
            case '"': out += "\\\""; break;
            case '\\': out += "\\\\"; break;
            case '\n': out += "\\n"; break;
            case '\r': out += "\\r"; break;
            case '\t': out += "\\t"; break;
            case '\b': out += "\\b"; break;
            case '\f': out += "\\f"; break;
            default:
                if (byte < 0x20) {
                    char buffer[8];
                    std::snprintf(buffer, sizeof buffer, "\\u%04x", byte);
                    out += buffer;
                } else {
                    out.push_back(raw);
                }
        }
    }
    out.push_back('"');
    return out;
}

std::string number(std::size_t value) { return std::to_string(value); }

Reply counts_reply(std::string_view text) {
    const Counts totals = count(text);
    std::string body = "{\"text\":" + quote(text);
    body += ",\"lines\":" + number(totals.lines);
    body += ",\"words\":" + number(totals.words);
    body += ",\"bytes\":" + number(totals.bytes);
    body += "}";
    return {200, std::move(body)};
}

Reply error_reply(int status, std::string code, std::optional<std::string> detail) {
    std::string body = "{\"error\":" + quote(code);
    if (detail.has_value()) {
        body += ",\"detail\":" + quote(*detail);
    }
    body += "}";
    return {status, std::move(body)};
}

int hex_value(char value) {
    if (value >= '0' && value <= '9') {
        return value - '0';
    }
    if (value >= 'a' && value <= 'f') {
        return value - 'a' + 10;
    }
    if (value >= 'A' && value <= 'F') {
        return value - 'A' + 10;
    }
    return -1;
}

std::string percent_decode(std::string_view raw) {
    std::string out;
    for (std::size_t index = 0; index < raw.size(); ++index) {
        char value = raw[index];
        if (value == '+') {
            out.push_back(' ');
        } else if (value == '%' && index + 2 < raw.size()) {
            const int high = hex_value(raw[index + 1]);
            const int low = hex_value(raw[index + 2]);
            if (high >= 0 && low >= 0) {
                out.push_back(static_cast<char>(high * 16 + low));
                index += 2;
            } else {
                out.push_back(value);
            }
        } else {
            out.push_back(value);
        }
    }
    return out;
}

std::optional<std::string> query_param(std::string_view query, std::string_view name) {
    std::size_t start = 0;
    while (start <= query.size()) {
        std::size_t end = query.find('&', start);
        if (end == std::string_view::npos) {
            end = query.size();
        }
        const std::string_view pair = query.substr(start, end - start);
        const std::size_t equals = pair.find('=');
        const std::string_view key = equals == std::string_view::npos ? pair : pair.substr(0, equals);
        if (key == name) {
            if (equals == std::string_view::npos) {
                return std::string();
            }
            return percent_decode(pair.substr(equals + 1));
        }
        if (end == query.size()) {
            break;
        }
        start = end + 1;
    }
    return std::nullopt;
}

}  // namespace

Reply route(std::string_view method, std::string_view path, std::string_view query,
            std::string_view body) {
    if (path == "/health" && method == "GET") {
        return {200, "{\"status\":\"ok\"}"};
    }
    if (path == "/stats" && method == "GET") {
        const std::optional<std::string> text = query_param(query, "text");
        if (!text.has_value()) {
            return error_reply(422, "missing_text", std::nullopt);
        }
        return counts_reply(*text);
    }
    if (path == "/stats" && method == "POST") {
        const TextField field = read_text(body);
        if (field.kind == TextKind::invalid) {
            return error_reply(422, "invalid_json", std::nullopt);
        }
        if (field.kind == TextKind::missing) {
            return error_reply(422, "missing_text", std::nullopt);
        }
        return counts_reply(field.text);
    }
    if (path == "/health" || path == "/stats") {
        return error_reply(405, "method_not_allowed", std::nullopt);
    }
    return error_reply(404, "not_found", "no route for " + std::string(method) + " " +
                                             std::string(path));
}

}  // namespace textstat

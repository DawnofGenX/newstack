import Foundation

/// The pure request-to-response mapping: no sockets, no framework, no HTTP.
enum Contract {
    struct Reply: Equatable {
        let status: Int
        let body: String
    }

    /// Routes one request.
    static func route(method: String, path: String, query: String?, body: String) -> Reply {
        if method == "GET", path == "/health" {
            return Reply(status: 200, body: "{\"status\":\"ok\"}")
        }
        if method == "GET", path == "/stats" {
            let params = parseQuery(query)
            guard let text = params["text"] else {
                return error(422, "missing_text", nil)
            }
            return statsReply(text)
        }
        if method == "POST", path == "/stats" {
            let read = JsonBody.read(body)
            switch read.kind {
            case .invalid:
                return error(422, "invalid_json", nil)
            case .missing:
                return error(422, "missing_text", nil)
            case .text:
                return statsReply(read.text ?? "")
            }
        }
        if path == "/health" || path == "/stats" {
            return error(405, "method_not_allowed", nil)
        }
        return error(404, "not_found", "no route for \(method) \(path)")
    }

    /// The reply for one counted text.
    static func statsReply(_ text: String) -> Reply {
        let counts = Counts.of(text)
        let body = "{\"text\":\(quote(text)),\"lines\":\(counts.lines),\"words\":\(counts.words),"
            + "\"bytes\":\(counts.bytes)}"
        return Reply(status: 200, body: body)
    }

    /// An error reply, with an optional `detail`.
    static func error(_ status: Int, _ code: String, _ detail: String?) -> Reply {
        var body = "{\"error\":\(quote(code))"
        if let detail {
            body += ",\"detail\":\(quote(detail))"
        }
        body += "}"
        return Reply(status: status, body: body)
    }

    /// Writes a JSON string literal, escaping everything JSON requires.
    static func quote(_ text: String) -> String {
        var out = "\""
        for scalar in text.unicodeScalars {
            switch scalar {
            case "\"": out += "\\\""
            case "\\": out += "\\\\"
            case "\n": out += "\\n"
            case "\r": out += "\\r"
            case "\t": out += "\\t"
            case UnicodeScalar(0x08): out += "\\b"
            case UnicodeScalar(0x0C): out += "\\f"
            default:
                if scalar.value < 0x20 {
                    out += String(format: "\\u%04x", scalar.value)
                } else {
                    out.unicodeScalars.append(scalar)
                }
            }
        }
        out += "\""
        return out
    }

    /// Splits a raw query string into decoded values; the first occurrence wins.
    static func parseQuery(_ query: String?) -> [String: String] {
        var params: [String: String] = [:]
        guard let query, !query.isEmpty else {
            return params
        }
        let raw = query.hasPrefix("?") ? String(query.dropFirst()) : query
        for pair in raw.split(separator: "&", omittingEmptySubsequences: true) {
            let parts = pair.split(separator: "=", maxSplits: 1, omittingEmptySubsequences: false)
            let name = decode(String(parts[0]))
            let value = parts.count > 1 ? decode(String(parts[1])) : ""
            if params[name] == nil {
                params[name] = value
            }
        }
        return params
    }

    /// Percent-decodes one component, as UTF-8, with `+` meaning a space.
    static func decode(_ raw: String) -> String {
        var bytes: [UInt8] = []
        let source = Array(raw.utf8)
        var index = 0
        while index < source.count {
            let byte = source[index]
            if byte == UInt8(ascii: "+") {
                bytes.append(0x20)
                index += 1
                continue
            }
            if byte == UInt8(ascii: "%"), index + 2 < source.count,
               let high = hexDigit(source[index + 1]), let low = hexDigit(source[index + 2])
            {
                bytes.append(high << 4 | low)
                index += 3
                continue
            }
            bytes.append(byte)
            index += 1
        }
        return String(bytes: bytes, encoding: .utf8) ?? raw
    }

    static func hexDigit(_ byte: UInt8) -> UInt8? {
        switch byte {
        case UInt8(ascii: "0")...UInt8(ascii: "9"): return byte - UInt8(ascii: "0")
        case UInt8(ascii: "a")...UInt8(ascii: "f"): return byte - UInt8(ascii: "a") + 10
        case UInt8(ascii: "A")...UInt8(ascii: "F"): return byte - UInt8(ascii: "A") + 10
        default: return nil
        }
    }
}

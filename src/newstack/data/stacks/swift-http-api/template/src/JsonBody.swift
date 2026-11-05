import Foundation

/// Reads the `text` member of a JSON object without a JSON library, keeping a JSON
/// number apart from a JSON string (only a string can be counted).
enum JsonBody {
    /// What a request body turned out to be.
    enum Kind: Equatable {
        /// Not JSON at all, or a JSON value that is not an object.
        case invalid
        /// A JSON object without a usable `text` string.
        case missing
        /// A JSON object with a `text` string.
        case text
    }

    struct Result: Equatable {
        let kind: Kind
        let text: String?

        static let invalid = Result(kind: .invalid, text: nil)
        static let missing = Result(kind: .missing, text: nil)
        static func found(_ text: String) -> Result { Result(kind: .text, text: text) }
    }

    private struct Malformed: Error {
        let message: String
    }

    private struct Reader {
        let bytes: [UInt8]
        var index = 0
        var found: String?
        var sawNonString = false

        init(_ body: String) {
            bytes = Array(body.utf8)
        }

        mutating func read() throws -> Result {
            skipSpace()
            try parseObject()
            skipSpace()
            if index != bytes.count {
                return .invalid
            }
            if sawNonString {
                return .missing
            }
            if let text = found {
                return .found(text)
            }
            return .missing
        }

        func fail(_ message: String) -> Malformed {
            Malformed(message: "\(message) at byte \(index)")
        }

        mutating func skipSpace() {
            while index < bytes.count, isSpace(bytes[index]) {
                index += 1
            }
        }

        func isSpace(_ byte: UInt8) -> Bool {
            byte == 0x20 || byte == 0x09 || byte == 0x0A || byte == 0x0D
        }

        mutating func look() throws -> UInt8 {
            guard index < bytes.count else {
                throw fail("unexpected end of input")
            }
            return bytes[index]
        }

        mutating func expect(_ wanted: UInt8) throws {
            guard try look() == wanted else {
                throw fail("expected \(Character(UnicodeScalar(wanted)))")
            }
            index += 1
        }

        mutating func parseObject() throws {
            try expect(UInt8(ascii: "{"))
            skipSpace()
            if try look() == UInt8(ascii: "}") {
                index += 1
                return
            }
            while true {
                skipSpace()
                let name = try parseString()
                skipSpace()
                try expect(UInt8(ascii: ":"))
                skipSpace()
                let isTextMember = name == "text"
                if isTextMember, try look() == UInt8(ascii: "\"") {
                    let value = try parseString()
                    if found == nil {
                        found = value
                    }
                } else {
                    if isTextMember, found == nil {
                        sawNonString = true
                    }
                    try skipValue()
                }
                skipSpace()
                let next = try look()
                if next == UInt8(ascii: ",") {
                    index += 1
                    continue
                }
                try expect(UInt8(ascii: "}"))
                return
            }
        }

        mutating func skipValue() throws {
            skipSpace()
            switch try look() {
            case UInt8(ascii: "{"):
                try skipContainer(open: UInt8(ascii: "{"), close: UInt8(ascii: "}"), isObject: true)
            case UInt8(ascii: "["):
                try skipContainer(open: UInt8(ascii: "["), close: UInt8(ascii: "]"), isObject: false)
            case UInt8(ascii: "\""):
                _ = try parseString()
            case UInt8(ascii: "t"):
                try literal("true")
            case UInt8(ascii: "f"):
                try literal("false")
            case UInt8(ascii: "n"):
                try literal("null")
            default:
                try parseNumber()
            }
        }

        mutating func literal(_ word: String) throws {
            let expected = Array(word.utf8)
            guard index + expected.count <= bytes.count,
                  Array(bytes[index..<(index + expected.count)]) == expected
            else {
                throw fail("expected \(word)")
            }
            index += expected.count
        }

        mutating func skipContainer(open: UInt8, close: UInt8, isObject: Bool) throws {
            try expect(open)
            skipSpace()
            if try look() == close {
                index += 1
                return
            }
            while true {
                if isObject {
                    skipSpace()
                    _ = try parseString()
                    skipSpace()
                    try expect(UInt8(ascii: ":"))
                }
                try skipValue()
                skipSpace()
                let next = try look()
                if next == UInt8(ascii: ",") {
                    index += 1
                    continue
                }
                try expect(close)
                return
            }
        }

        mutating func parseString() throws -> String {
            try expect(UInt8(ascii: "\""))
            var out: [UInt8] = []
            while true {
                let byte = try look()
                index += 1
                if byte == UInt8(ascii: "\"") {
                    guard let text = String(bytes: out, encoding: .utf8) else {
                        throw fail("invalid utf-8")
                    }
                    return text
                }
                if byte == UInt8(ascii: "\\") {
                    let escape = try look()
                    index += 1
                    switch escape {
                    case UInt8(ascii: "\""): out.append(UInt8(ascii: "\""))
                    case UInt8(ascii: "\\"): out.append(UInt8(ascii: "\\"))
                    case UInt8(ascii: "/"): out.append(UInt8(ascii: "/"))
                    case UInt8(ascii: "b"): out.append(0x08)
                    case UInt8(ascii: "f"): out.append(0x0C)
                    case UInt8(ascii: "n"): out.append(0x0A)
                    case UInt8(ascii: "r"): out.append(0x0D)
                    case UInt8(ascii: "t"): out.append(0x09)
                    case UInt8(ascii: "u"):
                        let code = try readEscape()
                        out.append(contentsOf: Array(String(UnicodeScalar(code)!).utf8))
                    default:
                        throw fail("unknown escape")
                    }
                    continue
                }
                if byte < 0x20 {
                    throw fail("control byte in a string")
                }
                out.append(byte)
            }
        }

        mutating func readEscape() throws -> UInt32 {
            let code = try readHex4()
            if code >= 0xD800, code <= 0xDBFF {
                if index + 1 < bytes.count,
                   bytes[index] == UInt8(ascii: "\\"), bytes[index + 1] == UInt8(ascii: "u")
                {
                    index += 2
                    let low = try readHex4()
                    if low >= 0xDC00, low <= 0xDFFF {
                        return 0x10000 + ((code - 0xD800) << 10) + (low - 0xDC00)
                    }
                    throw fail("lone high surrogate")
                }
                throw fail("lone high surrogate")
            }
            if code >= 0xDC00, code <= 0xDFFF {
                throw fail("lone low surrogate")
            }
            return code
        }

        mutating func readHex4() throws -> UInt32 {
            var value: UInt32 = 0
            for _ in 0..<4 {
                let byte = try look()
                index += 1
                let digit: UInt32
                switch byte {
                case UInt8(ascii: "0")...UInt8(ascii: "9"): digit = UInt32(byte - UInt8(ascii: "0"))
                case UInt8(ascii: "a")...UInt8(ascii: "f"): digit = UInt32(byte - UInt8(ascii: "a")) + 10
                case UInt8(ascii: "A")...UInt8(ascii: "F"): digit = UInt32(byte - UInt8(ascii: "A")) + 10
                default: throw fail("bad \\u escape")
                }
                value = value * 16 + digit
            }
            return value
        }

        mutating func parseNumber() throws {
            let start = index
            if index < bytes.count, bytes[index] == UInt8(ascii: "-") || bytes[index] == UInt8(ascii: "+") {
                index += 1
            }
            while index < bytes.count {
                let byte = bytes[index]
                if (byte >= UInt8(ascii: "0") && byte <= UInt8(ascii: "9")) || byte == UInt8(ascii: ".")
                    || byte == UInt8(ascii: "e") || byte == UInt8(ascii: "E")
                    || byte == UInt8(ascii: "+") || byte == UInt8(ascii: "-")
                {
                    index += 1
                    continue
                }
                break
            }
            if index == start {
                throw fail("expected a value")
            }
        }
    }

    /// Parses the body and reports what it holds.
    static func read(_ body: String) -> Result {
        var reader = Reader(body)
        do {
            return try reader.read()
        } catch {
            return .invalid
        }
    }
}

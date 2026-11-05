import Foundation

/// The three numbers the service reports, counted exactly as `wc` does.
struct Counts: Equatable {
    let lines: Int
    let words: Int
    let bytes: Int

    /// Counts one UTF-8 string: line = `\n`, word = maximal non-space run, bytes = UTF-8.
    static func of(_ text: String) -> Counts {
        var lines = 0
        var words = 0
        var inWord = false
        for byte in text.utf8 {
            if byte == 0x0A {
                lines += 1
            }
            if isSpace(byte) {
                inWord = false
            } else if !inWord {
                inWord = true
                words += 1
            }
        }
        return Counts(lines: lines, words: words, bytes: text.utf8.count)
    }

    static func isSpace(_ byte: UInt8) -> Bool {
        byte == 0x20 || byte == 0x09 || byte == 0x0A || byte == 0x0D || byte == 0x0B || byte == 0x0C
    }
}

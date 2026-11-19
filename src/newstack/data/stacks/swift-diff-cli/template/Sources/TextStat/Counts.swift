/// Which figures to print. `wc` prints all three when given no flag.
public struct Figures: Equatable, Sendable {
    public var lines: Bool
    public var words: Bool
    public var bytes: Bool

    public init(lines: Bool = false, words: Bool = false, bytes: Bool = false) {
        self.lines = lines
        self.words = words
        self.bytes = bytes
    }

    public static let all = Figures(lines: true, words: true, bytes: true)
    public static let none = Figures()
}

/// A `wc`-style tally: line feeds, maximal runs of non-whitespace, raw bytes.
public struct Counts: Equatable, Sendable {
    public var lines: Int
    public var words: Int
    public var bytes: Int

    public init(lines: Int, words: Int, bytes: Int) {
        self.lines = lines
        self.words = words
        self.bytes = bytes
    }

    public static let empty = Counts(lines: 0, words: 0, bytes: 0)

    public func add(_ other: Counts) -> Counts {
        Counts(lines: lines + other.lines, words: words + other.words, bytes: bytes + other.bytes)
    }

    /// The printed columns, in `wc` order, for the figures that were asked for.
    public func columns(_ figures: Figures) -> [Int] {
        var result: [Int] = []
        if figures.lines { result.append(lines) }
        if figures.words { result.append(words) }
        if figures.bytes { result.append(bytes) }
        return result
    }
}

public extension Counts {
    private static func isSpace(_ b: UInt8) -> Bool {
        b == 0x20 || b == 0x09 || b == 0x0A || b == 0x0D || b == 0x0B || b == 0x0C
    }

    /// Count raw bytes, so the numbers match `wc -l -w -c` on the same file:
    /// a line is a `\n` byte (a last line without a trailing newline is not
    /// counted), a word is a maximal run of non-whitespace bytes, and bytes
    /// are bytes, not characters.
    static func ofBytes(_ data: [UInt8]) -> Counts {
        var lines = 0
        var words = 0
        var inWord = false
        for b in data {
            if b == 0x0A { lines += 1 }
            if isSpace(b) {
                inWord = false
            } else if !inWord {
                words += 1
                inWord = true
            }
        }
        return Counts(lines: lines, words: words, bytes: data.count)
    }

    /// The column width `wc` uses: the widest figure printed anywhere in the output.
    static func width(rows: [Counts], figures: Figures) -> Int {
        rows.flatMap { $0.columns(figures) }
            .map { String($0).count }
            .max() ?? 0
    }

    /// Right-align every column to `width`, the way `wc` lines up its output.
    static func formatRow(figures: Figures, counts: Counts, label: String, width: Int) -> String {
        let numbers = counts.columns(figures).map { cell -> String in
            let text = String(cell)
            return String(repeating: " ", count: width - text.count) + text
        }
        return (numbers + [label]).joined(separator: " ")
    }
}

import Foundation

/// Every failure the converter reports, with a message meant for humans.
public struct RomanError: Error, Equatable, CustomStringConvertible {
    public let message: String

    public init(_ message: String) {
        self.message = message
    }

    public var description: String { message }
}

/// Conversion between integers 1...3999 and canonical Roman numerals.
public enum RomanNumeral {
    private static let table: [(Int, String)] = [
        (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
        (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
        (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
    ]

    private static let values: [Character: Int] = [
        "I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000,
    ]

    /// The canonical numeral for `value`.
    public static func format(_ value: Int) throws -> String {
        guard value >= 1, value <= 3999 else {
            throw RomanError("value must be between 1 and 3999, got \(value)")
        }
        var remaining = value
        var result = ""
        for (amount, symbol) in table {
            while remaining >= amount {
                result += symbol
                remaining -= amount
            }
        }
        return result
    }

    /// The integer value of a canonical numeral.
    public static func parse(_ text: String) throws -> Int {
        let numeral = text.uppercased()
        guard !numeral.isEmpty else {
            throw RomanError("empty numeral")
        }
        var total = 0
        var previous = 0
        for character in numeral.reversed() {
            guard let value = values[character] else {
                throw RomanError("invalid roman character '\(character)'")
            }
            if value < previous {
                total -= value
            } else {
                total += value
                previous = value
            }
        }
        let canonical = try format(total)
        guard canonical == numeral else {
            throw RomanError("\(text) is not a canonical numeral; did you mean \(canonical)?")
        }
        return total
    }
}

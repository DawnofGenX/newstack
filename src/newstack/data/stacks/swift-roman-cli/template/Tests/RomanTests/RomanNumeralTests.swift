import XCTest
import Roman

final class RomanNumeralTests: XCTestCase {
    func testFormatsTheCanonicalTable() throws {
        let cases: [(Int, String)] = [
            (1, "I"), (4, "IV"), (9, "IX"), (14, "XIV"), (40, "XL"),
            (90, "XC"), (400, "CD"), (900, "CM"), (1990, "MCMXC"),
            (2024, "MMXXIV"), (3999, "MMMCMXCIX"),
        ]
        for (value, numeral) in cases {
            XCTAssertEqual(try RomanNumeral.format(value), numeral)
        }
    }

    func testRoundTripsEverySupportedValue() throws {
        for value in 1...3999 {
            XCTAssertEqual(try RomanNumeral.parse(RomanNumeral.format(value)), value)
        }
    }

    func testParsesLowercaseInput() throws {
        XCTAssertEqual(try RomanNumeral.parse("mmxxiv"), 2024)
    }

    func testRejectsNonCanonicalNumerals() {
        for text in ["IIII", "VV", "IC", "XM", "XXXX"] {
            XCTAssertThrowsError(try RomanNumeral.parse(text), text) { error in
                XCTAssertTrue("\(error)".contains("canonical"), "\(text): \(error)")
            }
        }
    }

    func testRejectsInvalidCharactersAndEmptyInput() {
        XCTAssertThrowsError(try RomanNumeral.parse("ABC"))
        XCTAssertThrowsError(try RomanNumeral.parse(""))
    }

    func testRejectsOutOfRangeValues() {
        XCTAssertThrowsError(try RomanNumeral.format(0))
        XCTAssertThrowsError(try RomanNumeral.format(-3))
        XCTAssertThrowsError(try RomanNumeral.format(4000))
    }
}

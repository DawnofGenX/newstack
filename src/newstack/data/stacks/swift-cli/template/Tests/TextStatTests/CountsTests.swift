import XCTest
import TextStat

final class CountsTests: XCTestCase {
    private func counts(_ text: String) -> Counts {
        Counts.ofBytes([UInt8](text.utf8))
    }

    func testCountsNewlineTerminatedText() {
        XCTAssertEqual(counts("alpha beta\ngamma delta\n"), Counts(lines: 2, words: 4, bytes: 23))
    }

    func testLastLineWithoutNewlineIsNotCounted() {
        XCTAssertEqual(counts("alpha beta\ngamma"), Counts(lines: 1, words: 3, bytes: 16))
    }

    func testBytesAreBytesNotCharacters() {
        XCTAssertEqual(counts("héllo wörld\n"), Counts(lines: 1, words: 2, bytes: 14))
    }

    func testEmptyInput() {
        XCTAssertEqual(counts(""), Counts(lines: 0, words: 0, bytes: 0))
    }

    func testWhitespaceRuns() {
        XCTAssertEqual(counts("  one\t\ttwo  \n\n three \n"), Counts(lines: 3, words: 3, bytes: 22))
    }

    func testVerticalTabAndFormFeedAreWhitespace() {
        XCTAssertEqual(counts("a\u{0B}b\u{0C}c\n"), Counts(lines: 1, words: 3, bytes: 6))
    }

    func testAddSumsEveryColumn() {
        let a = Counts(lines: 1, words: 2, bytes: 3)
        let b = Counts(lines: 4, words: 5, bytes: 6)
        XCTAssertEqual(a.add(b), Counts(lines: 5, words: 7, bytes: 9))
    }
}

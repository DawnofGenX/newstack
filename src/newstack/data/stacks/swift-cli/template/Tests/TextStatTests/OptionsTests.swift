import XCTest
import TextStat

final class OptionsTests: XCTestCase {
    func testNoFlagsPrintsAllFigures() {
        let parsed = Options.parse(["a.txt"])
        XCTAssertEqual(parsed.figures, .all)
        XCTAssertEqual(parsed.files, ["a.txt"])
        XCTAssertEqual(parsed.status, .ok)
    }

    func testShortFlags() {
        XCTAssertEqual(Options.parse(["-l", "a"]).figures, Figures(lines: true))
        XCTAssertEqual(Options.parse(["-w", "a"]).figures, Figures(words: true))
        XCTAssertEqual(Options.parse(["-c", "a"]).figures, Figures(bytes: true))
    }

    func testLongFlags() {
        XCTAssertEqual(Options.parse(["--lines", "a"]).figures, Figures(lines: true))
        XCTAssertEqual(Options.parse(["--words", "a"]).figures, Figures(words: true))
        XCTAssertEqual(Options.parse(["--bytes", "a"]).figures, Figures(bytes: true))
    }

    func testClusteredShortFlags() {
        XCTAssertEqual(Options.parse(["-lw", "a"]).figures, Figures(lines: true, words: true))
        XCTAssertEqual(Options.parse(["-clw", "a"]).figures, .all)
    }

    func testHelpShortCircuits() {
        XCTAssertEqual(Options.parse(["-h"]).status, .help)
        XCTAssertEqual(Options.parse(["--help"]).status, .help)
        XCTAssertEqual(Options.parse(["--help", "--bogus"]).status, .help)
    }

    func testVersionShortCircuits() {
        XCTAssertEqual(Options.parse(["-V"]).status, .version)
        XCTAssertEqual(Options.parse(["--version"]).status, .version)
    }

    func testDashDashTerminatesOptions() {
        let parsed = Options.parse(["--", "-l"])
        XCTAssertEqual(parsed.files, ["-l"])
        XCTAssertEqual(parsed.status, .ok)
    }

    func testDashIsStdin() {
        let parsed = Options.parse(["-"])
        XCTAssertEqual(parsed.files, ["-"])
        XCTAssertEqual(parsed.status, .ok)
    }

    func testUnknownShortFlag() {
        XCTAssertEqual(Options.parse(["-x"]).status, .usageError("unknown option: -x"))
    }

    func testUnknownFlagInsideCluster() {
        XCTAssertEqual(Options.parse(["-lx"]).status, .usageError("unknown option: -x"))
    }

    func testUnknownLongFlag() {
        XCTAssertEqual(Options.parse(["--bogus"]).status, .usageError("unknown option: --bogus"))
    }
}

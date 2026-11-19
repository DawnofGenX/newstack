import XCTest
import TextStat

/// A reference type on purpose: the IO closures capture it, so the test can
/// observe what the CLI wrote after `run` returns.
private final class FakeIO {
    var files: [String: [UInt8]] = [:]
    var stdin: [UInt8] = []
    var out: [String] = []
    var err: [String] = []

    var io: IO {
        IO(
            readFile: { path in
                guard let data = self.files[path] else {
                    throw NSError(domain: "FakeIO", code: 2, userInfo: [NSLocalizedDescriptionKey: "no such file: \(path)"])
                }
                return data
            },
            readStdin: { self.stdin },
            out: { self.out.append($0) },
            err: { self.err.append($0) }
        )
    }
}

final class CLITests: XCTestCase {
    private func run(
        _ args: [String],
        files: [String: String] = [:],
        stdin: String = ""
    ) -> (code: Int32, out: [String], err: [String]) {
        let fake = FakeIO()
        for (name, text) in files {
            fake.files[name] = [UInt8](text.utf8)
        }
        fake.stdin = [UInt8](stdin.utf8)
        let code = CLI.run(args, io: fake.io)
        return (code, fake.out, fake.err)
    }

    func testSingleFilePrintsPaddedRow() {
        let result = run(["a.txt"], files: ["a.txt": "alpha beta\ngamma\n"])
        XCTAssertEqual(result.code, 0)
        XCTAssertEqual(result.out, [" 2  3 17 a.txt"])
        XCTAssertEqual(result.err, [])
    }

    func testTwoFilesPrintTotalRow() {
        let result = run(["a.txt", "b.txt"], files: ["a.txt": "alpha beta\ngamma\n", "b.txt": "one\n"])
        XCTAssertEqual(result.code, 0)
        XCTAssertEqual(result.out, [" 2  3 17 a.txt", " 1  1  4 b.txt", " 3  4 21 total"])
    }

    func testWidthSpansEveryRowIncludingTotal() {
        let result = run(["big.txt", "small.txt"], files: ["big.txt": String(repeating: "x ", count: 50), "small.txt": "y"])
        XCTAssertEqual(result.code, 0)
        XCTAssertEqual(result.out, ["  0  50 100 big.txt", "  0   1   1 small.txt", "  0  51 101 total"])
    }

    func testMissingFileStillCountsTheRestAndExitsOne() {
        let result = run(["missing.txt", "a.txt"], files: ["a.txt": "alpha beta\ngamma\n"])
        XCTAssertEqual(result.code, 1)
        XCTAssertEqual(result.out, [" 2  3 17 a.txt", " 2  3 17 total"])
        XCTAssertEqual(result.err, ["error: cannot open 'missing.txt'"])
    }

    func testStdinIsLabelledDash() {
        let result = run(["-"], stdin: "hi there\n")
        XCTAssertEqual(result.code, 0)
        XCTAssertEqual(result.out, ["1 2 9 -"])
    }

    func testNoFilesReadsStdin() {
        let result = run([], stdin: "hi there\n")
        XCTAssertEqual(result.code, 0)
        XCTAssertEqual(result.out, ["1 2 9 -"])
    }

    func testSingleFlagPrintsOnlyThatFigure() {
        let result = run(["-w", "a.txt"], files: ["a.txt": "alpha beta\ngamma\n"])
        XCTAssertEqual(result.code, 0)
        XCTAssertEqual(result.out, ["3 a.txt"])
    }

    func testVersion() {
        let result = run(["--version"])
        XCTAssertEqual(result.code, 0)
        XCTAssertEqual(result.out, ["0.1.0"])
    }

    func testHelp() {
        let result = run(["--help"])
        XCTAssertEqual(result.code, 0)
        XCTAssertEqual(result.out.count, 1)
        XCTAssertTrue(result.out[0].contains("Usage:"))
    }

    func testUnknownOptionIsAUsageError() {
        let result = run(["--bogus"])
        XCTAssertEqual(result.code, 2)
        XCTAssertEqual(result.out, [])
        XCTAssertEqual(result.err.count, 2)
        XCTAssertTrue(result.err[0].contains("--bogus"))
        XCTAssertTrue(result.err[1].contains("--help"))
    }

    func testHelpWinsOverUnknownOption() {
        let result = run(["--help", "--bogus"])
        XCTAssertEqual(result.code, 0)
    }
}

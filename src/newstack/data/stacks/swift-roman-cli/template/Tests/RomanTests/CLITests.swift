import XCTest
import Roman

private final class FakeIO {
    var stdin: [UInt8] = []
    var out: [String] = []
    var err: [String] = []

    var io: IO {
        IO(
            readFile: { path in
                throw NSError(domain: "FakeIO", code: 2, userInfo: [NSLocalizedDescriptionKey: "no such file: \(path)"])
            },
            readStdin: { self.stdin },
            out: { self.out.append($0) },
            err: { self.err.append($0) }
        )
    }
}

final class CLITests: XCTestCase {
    private func run(_ args: [String], stdin: String = "") -> (code: Int32, out: [String], err: [String]) {
        let fake = FakeIO()
        fake.stdin = [UInt8](stdin.utf8)
        let code = CLI.run(args, io: fake.io)
        return (code, fake.out, fake.err)
    }

    func testConvertsNumbersToNumerals() {
        let result = run(["--to", "2024"])
        XCTAssertEqual(result.code, 0)
        XCTAssertEqual(result.out, ["MMXXIV"])
    }

    func testConvertsNumeralsToNumbers() {
        let result = run(["--from", "MCMXC"])
        XCTAssertEqual(result.code, 0)
        XCTAssertEqual(result.out, ["1990"])
    }

    func testAutoDetectsBareValues() {
        let result = run(["14", "XIV"])
        XCTAssertEqual(result.code, 0)
        XCTAssertEqual(result.out, ["XIV", "14"])
    }

    func testReadsValuesFromStdinWhenNoArguments() {
        let result = run([], stdin: "9\nXL\n")
        XCTAssertEqual(result.code, 0)
        XCTAssertEqual(result.out, ["IX", "40"])
    }

    func testHelpExitsZero() {
        let result = run(["--help"])
        XCTAssertEqual(result.code, 0)
        XCTAssertTrue(result.out.joined().contains("Usage:"))
    }

    func testUnknownOptionExitsTwo() {
        let result = run(["--bogus"])
        XCTAssertEqual(result.code, 2)
        XCTAssertTrue(result.err.joined().contains("unknown option --bogus"))
    }

    func testBadValueExitsOne() {
        let result = run(["--from", "IIII"])
        XCTAssertEqual(result.code, 1)
        XCTAssertTrue(result.err.joined().contains("canonical"))
    }

    func testEmptyInputExitsOne() {
        let result = run([], stdin: "   \n")
        XCTAssertEqual(result.code, 1)
        XCTAssertTrue(result.err.joined().contains("nothing to convert"))
    }
}

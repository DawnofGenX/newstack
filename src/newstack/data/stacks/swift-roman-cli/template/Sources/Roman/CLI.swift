import Foundation

/// Every side effect the CLI needs, injected so tests can run offline.
public struct IO {
    public var readFile: (String) throws -> [UInt8]
    public var readStdin: () -> [UInt8]
    public var out: (String) -> Void
    public var err: (String) -> Void

    public init(
        readFile: @escaping (String) throws -> [UInt8],
        readStdin: @escaping () -> [UInt8],
        out: @escaping (String) -> Void,
        err: @escaping (String) -> Void
    ) {
        self.readFile = readFile
        self.readStdin = readStdin
        self.out = out
        self.err = err
    }
}

public enum CLI {
    static let usage = """
    Usage: {{ npm_name }} [options] [value...]

    Converts between integers and Roman numerals.

    Options:
      -t, --to N        print the numeral for the integer N
      -f, --from ROMAN  print the integer for the numeral ROMAN
      -h, --help        show this message

    Without arguments the values are read one per line from stdin. Bare values
    are converted automatically: digits are read as numbers, letters as numerals.
    """

    public static func run(_ args: [String], io: IO) -> Int32 {
        var mode = "auto"
        var values: [String] = []
        var index = 0

        while index < args.count {
            let argument = args[index]
            switch argument {
            case "-h", "--help":
                io.out(usage)
                return 0
            case "-t", "--to":
                guard index + 1 < args.count else {
                    return usageError(io, "\(argument) needs a value")
                }
                mode = "to"
                values.append(args[index + 1])
                index += 2
            case "-f", "--from":
                guard index + 1 < args.count else {
                    return usageError(io, "\(argument) needs a value")
                }
                mode = "from"
                values.append(args[index + 1])
                index += 2
            default:
                if argument.hasPrefix("-"), argument != "-" {
                    return usageError(io, "unknown option \(argument)")
                }
                values.append(argument)
                index += 1
            }
        }

        if values.isEmpty {
            let text = String(decoding: io.readStdin(), as: UTF8.self)
            values = text.split(separator: "\n")
                .map { $0.trimmingCharacters(in: .whitespaces) }
                .filter { !$0.isEmpty }
        }
        if values.isEmpty {
            io.err("{{ npm_name }}: nothing to convert")
            return 1
        }

        var status: Int32 = 0
        for value in values {
            do {
                let direction = mode == "auto" ? (Int(value) == nil ? "from" : "to") : mode
                if direction == "to" {
                    guard let number = Int(value) else {
                        io.err("{{ npm_name }}: not an integer: \(value)")
                        status = 1
                        continue
                    }
                    io.out(try RomanNumeral.format(number))
                } else {
                    io.out(String(try RomanNumeral.parse(value)))
                }
            } catch let error as RomanError {
                io.err("{{ npm_name }}: \(error.message)")
                status = 1
            } catch {
                io.err("{{ npm_name }}: \(error)")
                status = 1
            }
        }
        return status
    }

    private static func usageError(_ io: IO, _ message: String) -> Int32 {
        io.err("{{ npm_name }}: \(message)")
        io.err(usage)
        return 2
    }
}

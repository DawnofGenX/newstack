/// How a command line was resolved.
public enum Status: Equatable {
    case ok
    case help
    case version
    case usageError(String)
}

/// A parsed command line: what to print, what to read, and whether to run at all.
public struct Parsed: Equatable {
    public var figures: Figures
    public var files: [String]
    public var status: Status

    public init(figures: Figures, files: [String], status: Status) {
        self.figures = figures
        self.files = files
        self.status = status
    }
}

/// The failure half of a flag lookup: the message the CLI prints.
public struct UsageError: Error, Equatable {
    public let message: String

    public init(message: String) {
        self.message = message
    }
}

public enum Options {
    public static let version = "0.1.0"

    public static func usage(program: String) -> String {
        """
        Usage: \(program) [-l] [-w] [-c] [FILE...]

        Print newline, word and byte counts for each FILE, and a total line if
        more than one FILE is given. With no FILE, or when FILE is -, read
        standard input. With no flag, all three figures are printed.

          -l, --lines   print the newline count
          -w, --words   print the word count
          -c, --bytes   print the byte count
          -h, --help    print this help and exit
          -V, --version print the version and exit
        """
    }

    private static func appendFlag(_ figures: Figures, _ flag: Character) -> Figures? {
        switch flag {
        case "l": return Figures(lines: true, words: figures.words, bytes: figures.bytes)
        case "w": return Figures(lines: figures.lines, words: true, bytes: figures.bytes)
        case "c": return Figures(lines: figures.lines, words: figures.words, bytes: true)
        default: return nil
        }
    }

    /// Fold the short flags of one argument (`-lw`, or `-w` alone).
    private static func shortFlags(_ figures: Figures, _ arg: String) -> Result<Figures, UsageError> {
        var current = figures
        for flag in arg.dropFirst() {
            guard let next = appendFlag(current, flag) else {
                return .failure(UsageError(message: "unknown option: -\(flag)"))
            }
            current = next
        }
        return .success(current)
    }

    private static func longFlag(_ figures: Figures, _ arg: String) -> Result<Figures, UsageError> {
        switch arg {
        case "--lines": return .success(Figures(lines: true, words: figures.words, bytes: figures.bytes))
        case "--words": return .success(Figures(lines: figures.lines, words: true, bytes: figures.bytes))
        case "--bytes": return .success(Figures(lines: figures.lines, words: figures.words, bytes: true))
        default: return .failure(UsageError(message: "unknown option: \(arg)"))
        }
    }

    public static func parse(_ args: [String]) -> Parsed {
        var figures = Figures.none
        var files: [String] = []
        var onlyFiles = false

        for arg in args {
            if onlyFiles {
                files.append(arg)
                continue
            }
            switch arg {
            case "--":
                onlyFiles = true
            case "-h", "--help":
                return Parsed(figures: figures, files: files, status: .help)
            case "-V", "--version":
                return Parsed(figures: figures, files: files, status: .version)
            default:
                if arg.hasPrefix("--") {
                    switch longFlag(figures, arg) {
                    case .success(let updated):
                        figures = updated
                    case .failure(let error):
                        return Parsed(figures: figures, files: files, status: .usageError(error.message))
                    }
                } else if arg.hasPrefix("-") && arg.count > 1 {
                    switch shortFlags(figures, arg) {
                    case .success(let updated):
                        figures = updated
                    case .failure(let error):
                        return Parsed(figures: figures, files: files, status: .usageError(error.message))
                    }
                } else {
                    files.append(arg)
                }
            }
        }

        let chosen = figures == .none ? .all : figures
        return Parsed(figures: chosen, files: files, status: .ok)
    }
}

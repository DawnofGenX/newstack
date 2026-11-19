/// The I/O the CLI is allowed to touch. Tests inject fakes; the executable
/// wires up the real file system and standard streams.
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
    public static let program = "{{ npm_name }}"

    /// Run the tool. Returns the process exit code:
    /// 0 for success, help and version; 1 when a file could not be read
    /// (the other files are still counted); 2 for a usage error.
    public static func run(_ args: [String], io: IO) -> Int32 {
        let parsed = Options.parse(args)

        switch parsed.status {
        case .help:
            io.out(Options.usage(program: program))
            return 0
        case .version:
            io.out(Options.version)
            return 0
        case .usageError(let message):
            io.err("\(program): \(message)")
            io.err("Try '\(program) --help' for more information.")
            return 2
        case .ok:
            break
        }

        var rows: [(label: String, counts: Counts)] = []
        var failed = false

        // `wc` reads standard input when no FILE is given, or when FILE is `-`.
        let operands = parsed.files.isEmpty ? ["-"] : parsed.files

        for file in operands {
            let data: [UInt8]
            if file == "-" {
                data = io.readStdin()
            } else {
                do {
                    data = try io.readFile(file)
                } catch {
                    io.err("error: cannot open '\(file)'")
                    failed = true
                    continue
                }
            }
            rows.append((file, Counts.ofBytes(data)))
        }

        let figures = parsed.figures
        var allRows = rows
        if operands.count > 1 {
            let total = rows.reduce(Counts.empty) { $0.add($1.counts) }
            allRows.append((label: "total", counts: total))
        }
        let width = Counts.width(rows: allRows.map(\.counts), figures: figures)
        for row in allRows {
            io.out(Counts.formatRow(figures: figures, counts: row.counts, label: row.label, width: width))
        }

        return failed ? 1 : 0
    }
}

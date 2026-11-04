import Foundation
import TextStat

let io = IO(
    readFile: { path in
        let data = try Data(contentsOf: URL(fileURLWithPath: path))
        return [UInt8](data)
    },
    readStdin: {
        let data = FileHandle.standardInput.readDataToEndOfFile()
        return [UInt8](data)
    },
    out: { print($0) },
    err: { line in
        FileHandle.standardError.write(Data((line + "\n").utf8))
    }
)

exit(CLI.run(Array(CommandLine.arguments.dropFirst()), io: io))

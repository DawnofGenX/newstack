import Foundation

let environment = ProcessInfo.processInfo.environment
let host = environment["HOST"] ?? "127.0.0.1"
let raw = environment["PORT"] ?? "8080"
if CommandLine.arguments.contains("--selftest") {
    exit(Tests.run())
}
guard let port = Int(raw), port > 0, port < 65536 else {
    FileHandle.standardError.write(Data("PORT must be a number between 1 and 65535, got \(raw)\n".utf8))
    exit(2)
}
Server.serve(host: host, port: port)

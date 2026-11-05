import Glibc
import Foundation

/// The socket loop: one connection at a time on POSIX sockets, no framework.
enum Server {
    private static let maxBody = 65536
    private static let maxHead = 16384

    /// Binds and serves forever.
    static func serve(host: String, port: Int) -> Never {
        let fd = socket(AF_INET, Int32(SOCK_STREAM.rawValue), 0)
        guard fd >= 0 else {
            fatalError("socket: \(String(cString: strerror(errno)))")
        }
        var on: Int32 = 1
        setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &on, socklen_t(MemoryLayout<Int32>.size))

        var address = sockaddr_in()
        address.sin_family = sa_family_t(AF_INET)
        address.sin_port = in_port_t(port).bigEndian
        address.sin_addr.s_addr = inet_addr(host)
        let bound = withUnsafePointer(to: &address) { pointer in
            pointer.withMemoryRebound(to: sockaddr.self, capacity: 1) { raw in
                bind(fd, raw, socklen_t(MemoryLayout<sockaddr_in>.size))
            }
        }
        guard bound == 0 else {
            fatalError("bind \(host):\(port): \(String(cString: strerror(errno)))")
        }
        guard listen(fd, 16) == 0 else {
            fatalError("listen: \(String(cString: strerror(errno)))")
        }
        print("listening on http://\(host):\(port)")
        fflush(stdout)

        while true {
            var client = sockaddr_in()
            var length = socklen_t(MemoryLayout<sockaddr_in>.size)
            let connection = withUnsafeMutablePointer(to: &client) { pointer in
                pointer.withMemoryRebound(to: sockaddr.self, capacity: 1) { raw in
                    accept(fd, raw, &length)
                }
            }
            if connection < 0 {
                continue
            }
            handle(connection)
            close(connection)
        }
    }

    private static func handle(_ connection: Int32) {
        var buffer = [UInt8](repeating: 0, count: maxBody + maxHead)
        var used = 0
        while used < buffer.count {
            let read = readInto(connection, &buffer, used)
            if read <= 0 {
                break
            }
            used += read
            if headEnd(buffer, used) != nil {
                break
            }
        }
        guard let headEnd = headEnd(buffer, used) else {
            send(connection, status: 400, body: "{\"error\":\"invalid_json\"}")
            return
        }
        let head = String(decoding: buffer[0..<headEnd], as: UTF8.self)
        let lines = head.components(separatedBy: "\r\n")
        let requestLine = lines.first ?? ""
        let parts = requestLine.split(separator: " ", omittingEmptySubsequences: true)
        guard parts.count >= 2 else {
            send(connection, status: 400, body: "{\"error\":\"invalid_json\"}")
            return
        }
        let method = String(parts[0])
        let target = String(parts[1])
        var contentLength = 0
        for line in lines.dropFirst() {
            let halves = line.split(separator: ":", maxSplits: 1, omittingEmptySubsequences: false)
            if halves.count == 2, halves[0].lowercased() == "content-length" {
                contentLength = Int(halves[1].trimmingCharacters(in: .whitespaces)) ?? 0
            }
        }
        var bodyStart = headEnd + 4
        if contentLength > maxBody {
            send(connection, status: 413, body: "{\"error\":\"body_too_large\"}")
            return
        }
        while used - bodyStart < contentLength {
            let read = readInto(connection, &buffer, used)
            if read <= 0 {
                break
            }
            used += read
        }
        if bodyStart > used {
            bodyStart = used
        }
        let end = min(used, bodyStart + contentLength)
        let body = String(decoding: buffer[bodyStart..<end], as: UTF8.self)
        let (path, query) = splitTarget(target)
        let reply = Contract.route(method: method, path: path, query: query, body: body)
        send(connection, status: reply.status, body: reply.body)
    }

    private static func splitTarget(_ target: String) -> (String, String?) {
        guard let mark = target.firstIndex(of: "?") else {
            return (target, nil)
        }
        return (String(target[target.startIndex..<mark]), String(target[target.index(after: mark)...]))
    }

    private static func headEnd(_ buffer: [UInt8], _ used: Int) -> Int? {
        guard used >= 4 else {
            return nil
        }
        for index in 0...(used - 4) where buffer[index] == 0x0D && buffer[index + 1] == 0x0A
            && buffer[index + 2] == 0x0D && buffer[index + 3] == 0x0A
        {
            return index
        }
        return nil
    }

    private static func send(_ connection: Int32, status: Int, body: String) {
        let payload = Array(body.utf8)
        let head = "HTTP/1.1 \(status) \(reason(status))\r\n"
            + "content-type: application/json\r\n"
            + "content-length: \(payload.count)\r\n"
            + "connection: close\r\n\r\n"
        var out = Array(head.utf8)
        out.append(contentsOf: payload)
        out.withUnsafeBufferPointer { buffer in
            var sent = 0
            while sent < buffer.count {
                let wrote = Glibc.send(connection, buffer.baseAddress! + sent, buffer.count - sent, Int32(MSG_NOSIGNAL))
                if wrote <= 0 {
                    return
                }
                sent += wrote
            }
        }
    }

    /// Reads into `buffer` at `offset`, through a stable pointer to the whole array.
    private static func readInto(_ connection: Int32, _ buffer: inout [UInt8], _ offset: Int) -> Int {
        buffer.withUnsafeMutableBufferPointer { pointer in
            recv(connection, pointer.baseAddress! + offset, pointer.count - offset, 0)
        }
    }

    private static func reason(_ status: Int) -> String {
        switch status {
        case 200: return "OK"
        case 400: return "Bad Request"
        case 404: return "Not Found"
        case 405: return "Method Not Allowed"
        case 413: return "Payload Too Large"
        case 422: return "Unprocessable Entity"
        default: return "Internal Server Error"
        }
    }
}

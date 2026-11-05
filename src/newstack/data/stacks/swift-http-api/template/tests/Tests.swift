import Foundation

/// A dependency-free check suite: run the built binary with `--selftest`.
enum Tests {
    static var checks = 0
    static var failures: [String] = []

    static func check(_ name: String, _ ok: Bool) {
        checks += 1
        if !ok {
            failures.append(name)
            print("FAIL \(name)")
        }
    }

    static func counts(_ name: String, _ text: String, _ lines: Int, _ words: Int, _ bytes: Int) {
        let counts = Counts.of(text)
        check(name, counts.lines == lines && counts.words == words && counts.bytes == bytes)
    }

    static func reply(_ name: String, _ got: Contract.Reply, _ status: Int, _ body: String) {
        check(name, got.status == status && got.body == body)
    }

    static func contains(_ name: String, _ got: Contract.Reply, _ status: Int, _ needle: String) {
        check(name, got.status == status && got.body.contains(needle))
    }

    /// Runs every check and reports the tally.
    static func run() -> Int32 {
        counts("counts hello world", "hello world\n", 1, 2, 12)
        counts("counts empty", "", 0, 0, 0)
        counts("counts blank lines", "\n\nx\n", 3, 1, 4)
        counts("counts only spaces", "  \t ", 0, 0, 4)
        counts("counts no newline", "abc", 0, 1, 3)
        counts("counts utf-8", "héllo wörld\n", 1, 2, 14)
        counts("counts emoji", "🙂\n", 1, 1, 5)

        reply("health", Contract.route(method: "GET", path: "/health", query: nil, body: ""), 200, "{\"status\":\"ok\"}")
        let get = Contract.route(method: "GET", path: "/stats", query: "text=hello%20world%0A", body: "")
        contains("get stats lines", get, 200, "\"lines\":1")
        contains("get stats words", get, 200, "\"words\":2")
        contains("get stats bytes", get, 200, "\"bytes\":12")
        contains("get stats echoes the text", get, 200, "\"text\":\"hello world\\n\"")
        contains(
            "get stats with a leading ?",
            Contract.route(method: "GET", path: "/stats", query: "?text=a%20b%0Ac%0A", body: ""),
            200,
            "\"text\":\"a b\\nc\\n\"")
        contains("get stats empty value", Contract.route(method: "GET", path: "/stats", query: "text=", body: ""), 200, "\"lines\":0")
        contains("get stats missing text", Contract.route(method: "GET", path: "/stats", query: "", body: ""), 422, "missing_text")
        contains("get stats no query", Contract.route(method: "GET", path: "/stats", query: nil, body: ""), 422, "missing_text")
        contains(
            "post stats",
            Contract.route(method: "POST", path: "/stats", query: nil, body: "{\"text\": \"a b\\nc\\n\"}"),
            200,
            "\"words\":3")
        contains(
            "post stats padded",
            Contract.route(method: "POST", path: "/stats", query: nil, body: "{\"text\": \"  padded  \\n\"}"),
            200,
            "\"bytes\":11")
        contains("post stats missing text", Contract.route(method: "POST", path: "/stats", query: nil, body: "{}"), 422, "missing_text")
        contains(
            "post stats non-string text",
            Contract.route(method: "POST", path: "/stats", query: nil, body: "{\"text\": 42}"),
            422,
            "missing_text")
        contains(
            "post stats nested text ignored",
            Contract.route(method: "POST", path: "/stats", query: nil, body: "{\"meta\": {\"text\": \"x\"}}"),
            422,
            "missing_text")
        contains(
            "post stats invalid json",
            Contract.route(method: "POST", path: "/stats", query: nil, body: "nope"),
            422,
            "invalid_json")
        contains(
            "post stats trailing data",
            Contract.route(method: "POST", path: "/stats", query: nil, body: "{\"text\": \"a\"} tail"),
            422,
            "invalid_json")
        contains(
            "post stats escaped text",
            Contract.route(
                method: "POST", path: "/stats", query: nil, body: "{\"text\": \"h\\u00e9llo w\\u00f6rld\\n\"}"),
            200,
            "\"bytes\":14")
        contains(
            "post stats surrogate pair",
            Contract.route(method: "POST", path: "/stats", query: nil, body: "{\"text\": \"\\ud83d\\ude42\\n\"}"),
            200,
            "\"bytes\":5")
        reply(
            "unknown route",
            Contract.route(method: "GET", path: "/nope", query: nil, body: ""),
            404,
            "{\"error\":\"not_found\",\"detail\":\"no route for GET /nope\"}")
        reply(
            "wrong method",
            Contract.route(method: "DELETE", path: "/health", query: nil, body: ""),
            405,
            "{\"error\":\"method_not_allowed\"}")

        check("json text", JsonBody.read("{\"text\": \"a\"}").kind == .text)
        check("json number", JsonBody.read("{\"text\": 42}").kind == .missing)
        check("json object", JsonBody.read("{\"text\": {}}").kind == .missing)
        check("json array body", JsonBody.read("[1, 2]").kind == .invalid)
        check("json literal body", JsonBody.read("42").kind == .invalid)
        check("json empty body", JsonBody.read("").kind == .invalid)
        check("json nested value before text", JsonBody.read("{\"meta\": [1, {\"a\": null}], \"text\": \"x\"}").text == "x")

        print("checks: \(checks), passed: \(checks - failures.count), failed: \(failures.count)")
        return failures.isEmpty ? 0 : 1
    }
}

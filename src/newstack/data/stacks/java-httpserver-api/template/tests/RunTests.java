import java.util.ArrayList;
import java.util.List;
import {{ package_name }}.Contract;
import {{ package_name }}.Counts;
import {{ package_name }}.JsonBody;

/** A dependency-free test suite: {@code java -cp … RunTests}. */
public final class RunTests {

    private static final List<String> FAILURES = new ArrayList<>();
    private static int checks;

    private RunTests() {
    }

    private static void check(String name, boolean ok) {
        checks++;
        if (!ok) {
            FAILURES.add(name);
            System.out.println("FAIL " + name);
        }
    }

    private static void countsCase(String name, String text, int lines, int words, int bytes) {
        Counts counts = Counts.of(text);
        check(
                name,
                counts.lines() == lines && counts.words() == words && counts.bytes() == bytes);
    }

    private static void countsFails(String name, String text) {
        try {
            Counts.of(text);
            check(name, false);
        } catch (IllegalArgumentException expected) {
            check(name, true);
        }
    }

    private static boolean replyIs(Contract.Reply reply, int status, String body) {
        return reply.status() == status && reply.body().equals(body);
    }

    private static boolean contains(Contract.Reply reply, int status, String needle) {
        return reply.status() == status && reply.body().contains(needle);
    }

    /** Runs every check and exits non-zero when one fails. */
    public static void main(String[] args) {
        countsCase("counts hello world", "hello world\n", 1, 2, 12);
        countsCase("counts empty", "", 0, 0, 0);
        countsCase("counts blank lines", "\n\nx\n", 3, 1, 4);
        countsCase("counts only spaces", "  \t ", 0, 0, 4);
        countsCase("counts no newline", "abc", 0, 1, 3);
        countsCase("counts utf-8", "héllo wörld\n", 1, 2, 14);
        countsCase("counts emoji", "🙂\n", 1, 1, 5);
        countsFails("counts rejects null", null);

        check("health", replyIs(Contract.route("GET", "/health", null, ""), 200, "{\"status\":\"ok\"}"));
        check(
                "get stats",
                contains(
                        Contract.route("GET", "/stats", "text=hello%20world%0A", ""),
                        200,
                        "\"bytes\":12"));
        check(
                "get stats counts",
                contains(
                        Contract.route("GET", "/stats", "text=hello%20world%0A", ""),
                        200,
                        "\"lines\":1"));
        check(
                "get stats words",
                contains(
                        Contract.route("GET", "/stats", "text=hello%20world%0A", ""),
                        200,
                        "\"words\":2"));
        check(
                "get stats echoes the text",
                contains(
                        Contract.route("GET", "/stats", "?text=a%20b%0Ac%0A", ""),
                        200,
                        "\"text\":\"a b\\nc\\n\""));
        check("get stats empty value", contains(Contract.route("GET", "/stats", "text=", ""), 200, "\"lines\":0"));
        check(
                "get stats missing text",
                contains(Contract.route("GET", "/stats", "", ""), 422, "missing_text"));
        check(
                "post stats",
                contains(Contract.route("POST", "/stats", null, "{\"text\": \"a b\\nc\\n\"}"), 200, "\"words\":3"));
        check(
                "post stats padded",
                contains(
                        Contract.route("POST", "/stats", null, "{\"text\": \"  padded  \\n\"}"),
                        200,
                        "\"bytes\":11"));
        check(
                "post stats missing text",
                contains(Contract.route("POST", "/stats", null, "{}"), 422, "missing_text"));
        check(
                "post stats non-string text",
                contains(Contract.route("POST", "/stats", null, "{\"text\": 42}"), 422, "missing_text"));
        check(
                "post stats nested text ignored",
                contains(
                        Contract.route("POST", "/stats", null, "{\"meta\": {\"text\": \"x\"}}"),
                        422,
                        "missing_text"));
        check(
                "post stats invalid json",
                contains(Contract.route("POST", "/stats", null, "nope"), 422, "invalid_json"));
        check(
                "post stats trailing data",
                contains(Contract.route("POST", "/stats", null, "{\"text\": \"a\"} tail"), 422, "invalid_json"));
        check(
                "post stats escaped text",
                contains(
                        Contract.route("POST", "/stats", null, "{\"text\": \"h\\u00e9llo w\\u00f6rld\\n\"}"),
                        200,
                        "\"bytes\":14"));
        check(
                "post stats surrogate pair",
                contains(Contract.route("POST", "/stats", null, "{\"text\": \"\\ud83d\\ude42\\n\"}"), 200, "\"bytes\":5"));
        check(
                "unknown route",
                replyIs(
                        Contract.route("GET", "/nope", null, ""),
                        404,
                        "{\"error\":\"not_found\",\"detail\":\"no route for GET /nope\"}"));
        check(
                "wrong method",
                replyIs(Contract.route("DELETE", "/health", null, ""), 405, "{\"error\":\"method_not_allowed\"}"));
        check(
                "wrong method on stats",
                contains(Contract.route("PUT", "/stats", null, ""), 405, "method_not_allowed"));

        check("json text", JsonBody.read("{\"text\": \"a\"}").kind() == JsonBody.Kind.TEXT);
        check("json number", JsonBody.read("{\"text\": 42}").kind() == JsonBody.Kind.MISSING);
        check("json object", JsonBody.read("{\"text\": {}}").kind() == JsonBody.Kind.MISSING);
        check("json array body", JsonBody.read("[1, 2]").kind() == JsonBody.Kind.INVALID);
        check("json literal body", JsonBody.read("42").kind() == JsonBody.Kind.INVALID);
        check("json empty body", JsonBody.read("").kind() == JsonBody.Kind.INVALID);

        System.out.printf("checks: %d, passed: %d, failed: %d%n", checks, checks - FAILURES.size(), FAILURES.size());
        if (!FAILURES.isEmpty()) {
            System.exit(1);
        }
    }
}

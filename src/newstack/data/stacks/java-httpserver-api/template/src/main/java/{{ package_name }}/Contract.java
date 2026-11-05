package {{ package_name }};

import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.util.LinkedHashMap;
import java.util.Map;

/** The pure request-to-response mapping: no sockets, no framework, no HTTP. */
public final class Contract {

    /** A status code plus the exact bytes to send back. */
    public record Reply(int status, String body) {
    }

    private Contract() {
    }

    /** Routes one request. */
    public static Reply route(String method, String path, String query, String body) {
        if ("GET".equals(method) && "/health".equals(path)) {
            return new Reply(200, "{\"status\":\"ok\"}");
        }
        if ("GET".equals(method) && "/stats".equals(path)) {
            Map<String, String> params = parseQuery(query);
            if (!params.containsKey("text")) {
                return error(422, "missing_text", null);
            }
            return statsReply(params.get("text"));
        }
        if ("POST".equals(method) && "/stats".equals(path)) {
            JsonBody.Result read = JsonBody.read(body);
            return switch (read.kind()) {
                case INVALID -> error(422, "invalid_json", null);
                case MISSING -> error(422, "missing_text", null);
                case TEXT -> statsReply(read.text());
            };
        }
        if ("/health".equals(path) || "/stats".equals(path)) {
            return error(405, "method_not_allowed", null);
        }
        return error(404, "not_found", "no route for " + method + " " + path);
    }

    /** The reply for one counted text. */
    public static Reply statsReply(String text) {
        Counts counts = Counts.of(text);
        StringBuilder json = new StringBuilder("{\"text\":");
        quote(json, text);
        json.append(",\"lines\":").append(counts.lines())
                .append(",\"words\":").append(counts.words())
                .append(",\"bytes\":").append(counts.bytes())
                .append('}');
        return new Reply(200, json.toString());
    }

    /** An error reply, with an optional {@code detail}. */
    public static Reply error(int status, String code, String detail) {
        StringBuilder json = new StringBuilder("{\"error\":");
        quote(json, code);
        if (detail != null) {
            json.append(",\"detail\":");
            quote(json, detail);
        }
        json.append('}');
        return new Reply(status, json.toString());
    }

    /** Writes a JSON string literal, escaping everything JSON requires. */
    public static void quote(StringBuilder out, String text) {
        out.append('"');
        for (int i = 0; i < text.length(); i++) {
            char c = text.charAt(i);
            switch (c) {
                case '"' -> out.append("\\\"");
                case '\\' -> out.append("\\\\");
                case '\n' -> out.append("\\n");
                case '\r' -> out.append("\\r");
                case '\t' -> out.append("\\t");
                case '\b' -> out.append("\\b");
                case '\f' -> out.append("\\f");
                default -> {
                    if (c < 0x20) {
                        out.append(String.format("\\u%04x", (int) c));
                    } else {
                        out.append(c);
                    }
                }
            }
        }
        out.append('"');
    }

    /** Splits a raw query string into decoded values; the first occurrence wins. */
    public static Map<String, String> parseQuery(String query) {
        Map<String, String> params = new LinkedHashMap<>();
        if (query == null || query.isEmpty()) {
            return params;
        }
        String raw = query.startsWith("?") ? query.substring(1) : query;
        for (String pair : raw.split("&")) {
            if (pair.isEmpty()) {
                continue;
            }
            int equals = pair.indexOf('=');
            String name = equals < 0 ? pair : pair.substring(0, equals);
            String value = equals < 0 ? "" : pair.substring(equals + 1);
            String key = decode(name);
            if (!params.containsKey(key)) {
                params.put(key, decode(value));
            }
        }
        return params;
    }

    private static String decode(String raw) {
        return URLDecoder.decode(raw, StandardCharsets.UTF_8);
    }
}

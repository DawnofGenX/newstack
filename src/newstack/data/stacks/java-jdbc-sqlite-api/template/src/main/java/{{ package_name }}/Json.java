package {{ package_name }};

import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.util.List;

public final class Json {
    private Json() {}

    public static String escape(String value) {
        StringBuilder out = new StringBuilder();
        for (int i = 0; i < value.length(); i++) {
            char c = value.charAt(i);
            switch (c) {
                case '"' -> out.append("\\\"");
                case '\\' -> out.append("\\\\");
                case '\n' -> out.append("\\n");
                case '\r' -> out.append("\\r");
                case '\t' -> out.append("\\t");
                default -> {
                    if (c < 0x20) {
                        out.append(String.format("\\u%04x", (int) c));
                    } else {
                        out.append(c);
                    }
                }
            }
        }
        return out.toString();
    }

    public static String toJson(Note note) {
        return "{\"title\":\"" + escape(note.title()) + "\",\"body\":\"" + escape(note.body()) + "\"}";
    }

    public static String toJson(List<Note> notes) {
        StringBuilder out = new StringBuilder("[");
        for (int i = 0; i < notes.size(); i++) {
            if (i > 0) {
                out.append(",");
            }
            out.append(toJson(notes.get(i)));
        }
        out.append("]");
        return out.toString();
    }

    public static String field(String json, String name) {
        if (json == null) {
            return null;
        }
        String pattern = "\"" + name + "\"";
        int key = json.indexOf(pattern);
        if (key < 0) {
            return null;
        }
        int colon = json.indexOf(':', key + pattern.length());
        if (colon < 0) {
            return null;
        }
        int start = json.indexOf('"', colon + 1);
        if (start < 0) {
            return null;
        }
        StringBuilder value = new StringBuilder();
        boolean escape = false;
        for (int i = start + 1; i < json.length(); i++) {
            char c = json.charAt(i);
            if (escape) {
                switch (c) {
                    case 'n' -> value.append('\n');
                    case 'r' -> value.append('\r');
                    case 't' -> value.append('\t');
                    case '"' -> value.append('"');
                    case '\\' -> value.append('\\');
                    default -> value.append(c);
                }
                escape = false;
            } else if (c == '\\') {
                escape = true;
            } else if (c == '"') {
                return value.toString();
            } else {
                value.append(c);
            }
        }
        return null;
    }

    public static String queryParam(String query, String name) {
        if (query == null) {
            return null;
        }
        for (String pair : query.split("&")) {
            String[] parts = pair.split("=", 2);
            if (parts.length == 2 && parts[0].equals(name)) {
                return URLDecoder.decode(parts[1], StandardCharsets.UTF_8);
            }
        }
        return null;
    }
}
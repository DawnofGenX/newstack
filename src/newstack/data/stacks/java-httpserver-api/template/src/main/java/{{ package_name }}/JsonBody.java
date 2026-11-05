package {{ package_name }};

/**
 * Reads the {@code text} member of a JSON object without a JSON library, keeping a
 * JSON number apart from a JSON string (only a string can be counted).
 */
public final class JsonBody {

    /** What a request body turned out to be. */
    public enum Kind {
        /** Not JSON at all, or a JSON value that is not an object. */
        INVALID,
        /** A JSON object without a usable {@code text} string. */
        MISSING,
        /** A JSON object with a {@code text} string. */
        TEXT
    }

    /** The verdict on a request body. */
    public record Result(Kind kind, String text) {
    }

    private final String text;
    private int index;
    private boolean found;
    private boolean notAString;
    private String captured;

    private JsonBody(String text) {
        this.text = text;
    }

    private static final class Malformed extends RuntimeException {
        private static final long serialVersionUID = 1L;

        Malformed(String message) {
            super(message);
        }
    }

    /** Parses the body and reports what it holds. */
    public static Result read(String body) {
        JsonBody reader = new JsonBody(body == null ? "" : body);
        try {
            reader.skipSpace();
            reader.parseObject();
            reader.skipSpace();
            if (reader.index != reader.text.length()) {
                return new Result(Kind.INVALID, null);
            }
        } catch (Malformed error) {
            return new Result(Kind.INVALID, null);
        }
        if (reader.notAString) {
            return new Result(Kind.MISSING, null);
        }
        return reader.found ? new Result(Kind.TEXT, reader.captured) : new Result(Kind.MISSING, null);
    }

    private void fail(String message) {
        throw new Malformed(message + " at byte " + index);
    }

    private void skipSpace() {
        while (index < text.length() && Character.isWhitespace(text.charAt(index))) {
            index++;
        }
    }

    private char look() {
        if (index >= text.length()) {
            fail("unexpected end of input");
        }
        return text.charAt(index);
    }

    private void expect(char wanted) {
        if (look() != wanted) {
            fail("expected '" + wanted + "'");
        }
        index++;
    }

    private void parseObject() {
        expect('{');
        skipSpace();
        if (look() == '}') {
            index++;
            return;
        }
        while (true) {
            skipSpace();
            String name = parseString();
            skipSpace();
            expect(':');
            skipSpace();
            boolean isTextMember = name.equals("text");
            if (isTextMember && look() == '"') {
                String value = parseString();
                if (!found) {
                    found = true;
                    captured = value;
                }
            } else {
                if (isTextMember && !found) {
                    notAString = true;
                }
                skipValue();
            }
            skipSpace();
            char next = look();
            if (next == ',') {
                index++;
                continue;
            }
            expect('}');
            return;
        }
    }

    private void skipValue() {
        skipSpace();
        char c = look();
        switch (c) {
            case '{' -> skipObject();
            case '[' -> skipArray();
            case '"' -> parseString();
            case 't' -> {
                literal("true");
            }
            case 'f' -> {
                literal("false");
            }
            case 'n' -> {
                literal("null");
            }
            default -> parseNumber();
        }
    }

    private void literal(String word) {
        if (!text.startsWith(word, index)) {
            fail("expected " + word);
        }
        index += word.length();
    }

    private void skipObject() {
        expect('{');
        skipSpace();
        if (look() == '}') {
            index++;
            return;
        }
        while (true) {
            skipSpace();
            parseString();
            skipSpace();
            expect(':');
            skipValue();
            skipSpace();
            if (look() == ',') {
                index++;
                continue;
            }
            expect('}');
            return;
        }
    }

    private void skipArray() {
        expect('[');
        skipSpace();
        if (look() == ']') {
            index++;
            return;
        }
        while (true) {
            skipValue();
            skipSpace();
            if (look() == ',') {
                index++;
                continue;
            }
            expect(']');
            return;
        }
    }

    private String parseString() {
        expect('"');
        StringBuilder out = new StringBuilder();
        while (true) {
            char c = look();
            index++;
            if (c == '"') {
                return out.toString();
            }
            if (c == '\\') {
                char escape = look();
                index++;
                switch (escape) {
                    case '"' -> out.append('"');
                    case '\\' -> out.append('\\');
                    case '/' -> out.append('/');
                    case 'b' -> out.append('\b');
                    case 'f' -> out.append('\f');
                    case 'n' -> out.append('\n');
                    case 'r' -> out.append('\r');
                    case 't' -> out.append('\t');
                    case 'u' -> out.appendCodePoint(readEscape());
                    default -> fail("unknown escape");
                }
                continue;
            }
            if (c < 0x20) {
                fail("control character in a string");
            }
            out.append(c);
        }
    }

    private int readEscape() {
        int code = readHex4();
        if (Character.isHighSurrogate((char) code)) {
            if (index + 1 < text.length() && text.charAt(index) == '\\' && text.charAt(index + 1) == 'u') {
                index += 2;
                int low = readHex4();
                if (Character.isLowSurrogate((char) low)) {
                    return Character.toCodePoint((char) code, (char) low);
                }
                fail("lone high surrogate");
            }
            fail("lone high surrogate");
        }
        if (Character.isLowSurrogate((char) code)) {
            fail("lone low surrogate");
        }
        return code;
    }

    private int readHex4() {
        int value = 0;
        for (int i = 0; i < 4; i++) {
            if (index >= text.length()) {
                fail("short \\u escape");
            }
            int digit = Character.digit(text.charAt(index), 16);
            if (digit < 0) {
                fail("bad \\u escape");
            }
            value = value * 16 + digit;
            index++;
        }
        return value;
    }

    private void parseNumber() {
        int start = index;
        if (index < text.length() && (text.charAt(index) == '-' || text.charAt(index) == '+')) {
            index++;
        }
        boolean any = false;
        while (index < text.length()) {
            char c = text.charAt(index);
            if (Character.isDigit(c) || c == '.' || c == 'e' || c == 'E' || c == '+' || c == '-') {
                index++;
                any = true;
                continue;
            }
            break;
        }
        if (!any) {
            index = start;
            fail("expected a value");
        }
    }
}

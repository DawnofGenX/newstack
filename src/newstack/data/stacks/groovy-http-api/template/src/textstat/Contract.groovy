package textstat

/** The route table, pure: method/path/query/body in, status and body out. */
class Contract {
    static Reply route(String method, String path, String query, String body) {
        if (path == '/health') {
            if (method == 'GET') {
                return reply(200, '{"status":"ok"}')
            }
            return methodNotAllowed()
        }
        if (path == '/stats') {
            if (method == 'GET') {
                String text = queryParam(query, 'text')
                if (text == null) {
                    return error(422, 'missing_text', null)
                }
                return stats(text)
            }
            if (method == 'POST') {
                Map parsed = Json.readText(body)
                switch (parsed.kind) {
                    case Json.Kind.TEXT:
                        return stats((String) parsed.text)
                    case Json.Kind.MISSING:
                        return error(422, 'missing_text', null)
                    default:
                        return error(422, 'invalid_json', null)
                }
            }
            return methodNotAllowed()
        }
        return notFound(method, path)
    }

    private static Reply stats(String text) {
        Counts counts = Counts.of(text)
        return reply(200, '{"text":' + quote(text) + ',"lines":' + counts.lines +
            ',"words":' + counts.words + ',"bytes":' + counts.bytes + '}')
    }

    private static Reply reply(int status, String body) {
        return new Reply(status: status, body: body)
    }

    private static Reply error(int status, String code, String detail) {
        String body = detail == null
            ? '{"error":' + quote(code) + '}'
            : '{"error":' + quote(code) + ',"detail":' + quote(detail) + '}'
        return reply(status, body)
    }

    private static Reply methodNotAllowed() {
        return error(405, 'method_not_allowed', null)
    }

    private static Reply notFound(String method, String path) {
        return error(404, 'not_found', 'no route for ' + method + ' ' + path)
    }

    static String quote(String text) {
        StringBuilder out = new StringBuilder('"')
        for (int index = 0; index < text.length(); index++) {
            char character = text.charAt(index)
            switch (character) {
                case (char) '"': out.append('\\"'); break
                case (char) '\\': out.append('\\\\'); break
                case (char) '\n': out.append('\\n'); break
                case (char) '\r': out.append('\\r'); break
                case (char) '\t': out.append('\\t'); break
                default:
                    if (character < (char) 0x20) {
                        out.append(String.format('\\u%04x', (int) character))
                    } else {
                        out.append(character)
                    }
            }
        }
        out.append('"')
        return out.toString()
    }

    /** Reads one pair of the query string, decoding "+" and "%XX". Null when absent. */
    static String queryParam(String query, String name) {
        if (query == null || query.isEmpty()) {
            return null
        }
        for (String pair : query.split('&')) {
            int equals = pair.indexOf('=')
            String key = equals < 0 ? pair : pair.substring(0, equals)
            if (key != name) {
                continue
            }
            String raw = equals < 0 ? '' : pair.substring(equals + 1)
            return java.net.URLDecoder.decode(raw, 'UTF-8')
        }
        return null
    }
}

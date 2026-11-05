package textstat

import groovy.json.JsonSlurper

/** Reads the "text" field, keeping a string apart from a number. */
class Json {
    enum Kind { INVALID, MISSING, TEXT }

    static Map readText(String body) {
        Object parsed
        try {
            parsed = new JsonSlurper().parseText(body == null ? '' : body)
        } catch (Exception ignored) {
            return [kind: Kind.INVALID, text: null]
        }
        // JsonSlurper turns a JSON number into a BigDecimal/Integer and a JSON
        // string into a String, so instanceof is the whole distinction.
        if (!(parsed instanceof Map)) {
            return [kind: Kind.INVALID, text: null]
        }
        if (!parsed.containsKey('text')) {
            return [kind: Kind.MISSING, text: null]
        }
        Object value = parsed['text']
        if (!(value instanceof String)) {
            return [kind: Kind.MISSING, text: null]
        }
        return [kind: Kind.TEXT, text: (String) value]
    }
}

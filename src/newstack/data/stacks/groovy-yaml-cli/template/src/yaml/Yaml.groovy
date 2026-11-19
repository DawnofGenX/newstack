// GROOVY_YAML_CLI_MARKER_7b2d9e
package yaml

class Yaml {
    static Object parse(String text) {
        List lines = []
        text.eachLine { raw ->
            String t = raw.replaceAll(/\r$/, '')
            String trimmed = t.trim()
            if (trimmed && !trimmed.startsWith('#')) {
                int indent = t.takeWhile { it == ' ' }.length()
                lines << [indent: indent, text: trimmed]
            }
        }
        if (lines.isEmpty()) return [:]
        Parser p = new Parser(lines)
        return p.parseMap(0)
    }

    static List<String> flatten(Object obj) {
        List<String> out = []
        flattenInto(obj, '', out)
        return out
    }

    private static void flattenInto(Object obj, String prefix, List<String> out) {
        if (obj instanceof Map) {
            obj.each { k, v ->
                String path = prefix ? "${prefix}.${k}" : "${k}"
                flattenInto(v, path, out)
            }
        } else if (obj instanceof List) {
            obj.eachWithIndex { v, i ->
                flattenInto(v, "${prefix}[${i}]", out)
            }
        } else {
            String val = (obj == null) ? '' : obj.toString()
            out << "${prefix}: ${val}".toString()
        }
    }

    static String render(String text) {
        Object obj = parse(text)
        return flatten(obj).join('\n')
    }

    static class Parser {
        List lines
        int idx = 0

        Parser(List lines) { this.lines = lines }

        Map parseMap(int base) {
            Map result = [:]
            while (idx < lines.size()) {
                def e = lines[idx]
                if (e.indent < base) break
                if (e.indent > base) { idx++; continue }
                String line = e.text
                int colon = line.indexOf(':')
                if (colon < 0) { idx++; continue }
                String key = line.substring(0, colon).trim()
                String rest = line.substring(colon + 1).trim()
                idx++
                if (rest) {
                    result[key] = parseScalar(rest)
                } else {
                    if (idx < lines.size() && lines[idx].indent > base) {
                        int childIndent = lines[idx].indent
                        if (lines[idx].text.startsWith('- ')) {
                            result[key] = parseList(childIndent)
                        } else {
                            result[key] = parseMap(childIndent)
                        }
                    } else {
                        result[key] = null
                    }
                }
            }
            return result
        }

        List parseList(int base) {
            List result = []
            while (idx < lines.size()) {
                def e = lines[idx]
                if (e.indent < base) break
                if (e.indent != base) break
                if (!e.text.startsWith('- ')) break
                String content = e.text.substring(2).trim()
                idx++
                if (content == '') {
                    if (idx < lines.size() && lines[idx].indent > base) {
                        int ci = lines[idx].indent
                        if (lines[idx].text.startsWith('- ')) {
                            result << parseList(ci)
                        } else {
                            result << parseMap(ci)
                        }
                    } else {
                        result << null
                    }
                } else if (content.contains(':')) {
                    // inline simple key: value -> treat as one-item map? skip; parse as scalar
                    result << parseScalar(content)
                } else {
                    result << parseScalar(content)
                }
            }
            return result
        }

        static Object parseScalar(String s) {
            String v = s.trim()
            if (v == 'null' || v == '~' || v == '') return null
            if (v == 'true') return true
            if (v == 'false') return false
            if (v ==~ /^-?\d+$/) return Long.valueOf(v)
            if (v ==~ /^-?\d+\.\d+$/) return Double.valueOf(v)
            // strip quotes
            if ((v.startsWith('"') && v.endsWith('"')) || (v.startsWith("'") && v.endsWith("'"))) {
                return v.substring(1, v.length() - 1)
            }
            return v
        }
    }
}
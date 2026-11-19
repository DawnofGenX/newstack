class IniReader {
    static Object typed(String raw) {
        raw = raw.trim()
        if (raw == "true") return Boolean.TRUE
        if (raw == "false") return Boolean.FALSE
        if (raw ==~ /-?\d+/) {
            try { return Integer.valueOf(raw) } catch (Exception ignored) {}
        }
        if (raw ==~ /-?\d+\.\d+([eE][+-]?\d+)?/) {
            try { return Double.valueOf(raw) } catch (Exception ignored) {}
        }
        if (raw.startsWith("\"") && raw.endsWith("\"") && raw.length() >= 2) {
            return raw.substring(1, raw.length() - 1)
        }
        return raw
    }

    static Map parse(String text) {
        def result = [:]
        def section = ""
        text.eachLine { line ->
            def trimmed = line.trim()
            if (trimmed.isEmpty()) return
            if (trimmed.startsWith(";") || trimmed.startsWith("#")) return
            if (trimmed.startsWith("[") && trimmed.endsWith("]")) {
                section = trimmed.substring(1, trimmed.length() - 1).trim()
                if (!result.containsKey(section)) result[section] = [:]
                return
            }
            def eq = trimmed.indexOf("=")
            if (eq < 0) throw new IllegalArgumentException("invalid line: ${trimmed}")
            def key = trimmed.substring(0, eq).trim()
            def value = trimmed.substring(eq + 1).trim()
            if (section == "" && !result.containsKey("")) result[""] = [:]
            if (!result.containsKey(section)) result[section] = [:]
            result[section][key] = typed(value)
        }
        if (!result.containsKey("")) result[""] = [:]
        return result
    }

    static Object get(Map data, String key) {
        def parts = key.split(/\./, 2)
        if (parts.length == 2) {
            def section = parts[0]
            def name = parts[1]
            if (!data.containsKey(section)) throw new IllegalArgumentException("unknown key: ${key}")
            if (!data[section].containsKey(name)) throw new IllegalArgumentException("unknown key: ${key}")
            return data[section][name]
        }
        // top-level/global: search all sections? Prefer unnamed section then any
        if (data.containsKey("") && data[""].containsKey(key)) return data[""][key]
        for (def e : data.entrySet()) {
            if (e.value.containsKey(key)) return e.value[key]
        }
        throw new IllegalArgumentException("unknown key: ${key}")
    }

    static String format(Object value) {
        if (value == null) return "null"
        return value.toString()
    }
}

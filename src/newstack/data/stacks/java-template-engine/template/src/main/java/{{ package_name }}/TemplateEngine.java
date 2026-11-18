package {{ package_name }};

// java-template-engine

import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public final class TemplateEngine {
    // java-template-engine
    private static final Pattern PLACEHOLDER = Pattern.compile("\\{\\{\\s*([A-Za-z_][A-Za-z0-9_]*)\\s*\\}\\}");

    private TemplateEngine() {}

    public static String render(String template, Map<String, String> vars) {
        if (template == null) return null;
        Matcher m = PLACEHOLDER.matcher(template);
        StringBuffer sb = new StringBuffer();
        while (m.find()) {
            String key = m.group(1);
            String val = vars == null ? null : vars.get(key);
            if (val == null) {
                // leave unknown placeholder untouched
                m.appendReplacement(sb, Matcher.quoteReplacement(m.group(0)));
            } else {
                m.appendReplacement(sb, Matcher.quoteReplacement(val));
            }
        }
        m.appendTail(sb);
        return sb.toString();
    }
}
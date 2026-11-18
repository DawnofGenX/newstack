package {{ package_name }};

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Iterator;
import java.util.Map;

public final class Flattener {
    private Flattener() {}

    public static ObjectNode flatten(JsonNode root) {
        ObjectMapper mapper = new ObjectMapper();
        ObjectNode out = mapper.createObjectNode();
        flatten("", root, out);
        return out;
    }

    private static void flatten(String prefix, JsonNode node, ObjectNode out) {
        if (node == null || node.isNull()) {
            if (!prefix.isEmpty()) {
                out.putNull(prefix);
            }
            return;
        }
        if (node.isObject()) {
            Iterator<Map.Entry<String, JsonNode>> it = node.fields();
            while (it.hasNext()) {
                Map.Entry<String, JsonNode> e = it.next();
                String key = prefix.isEmpty() ? e.getKey() : prefix + "." + e.getKey();
                flatten(key, e.getValue(), out);
            }
            if (prefix.isEmpty() && !node.fieldNames().hasNext()) {
                // empty object stays empty
            }
        } else if (node.isArray()) {
            for (int i = 0; i < node.size(); i++) {
                String key = prefix.isEmpty() ? String.valueOf(i) : prefix + "." + i;
                flatten(key, node.get(i), out);
            }
        } else {
            if (prefix.isEmpty()) {
                // scalar root: store under empty? skip; caller handles
                return;
            }
            out.set(prefix, node);
        }
    }
}

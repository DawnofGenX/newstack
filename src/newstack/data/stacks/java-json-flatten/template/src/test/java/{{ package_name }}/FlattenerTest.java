package {{ package_name }};

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;

class FlattenerTest {
    private final ObjectMapper mapper = new ObjectMapper();

    @Test
    void flattensNestedObject() throws Exception {
        JsonNode root = mapper.readTree("{\"a\":{\"b\":1,\"c\":\"x\"},\"d\":true}");
        ObjectNode flat = Flattener.flatten(root);
        assertEquals(1, flat.get("a.b").asInt());
        assertEquals("x", flat.get("a.c").asText());
        assertEquals(true, flat.get("d").asBoolean());
    }

    @Test
    void flattensArraysWithIndices() throws Exception {
        JsonNode root = mapper.readTree("{\"items\":[10,20]}");
        ObjectNode flat = Flattener.flatten(root);
        assertEquals(10, flat.get("items.0").asInt());
        assertEquals(20, flat.get("items.1").asInt());
    }

    @Test
    void emptyObjectStaysEmpty() throws Exception {
        JsonNode root = mapper.readTree("{}");
        ObjectNode flat = Flattener.flatten(root);
        assertEquals(0, flat.size());
    }
}

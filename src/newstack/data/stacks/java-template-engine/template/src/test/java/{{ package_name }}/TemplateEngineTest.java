package {{ package_name }};

import org.junit.jupiter.api.Test;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;

class TemplateEngineTest {
    @Test
    void rendersPlaceholders() {
        String out = TemplateEngine.render("Hello {{! name }}! {{! n }}", Map.of("name", "World", "n", "42"));
        assertEquals("Hello World! 42", out);
    }

    @Test
    void leavesUnknown() {
        assertEquals("hi {{!x}}", TemplateEngine.render("hi {{!x}}", Map.of()));
    }

    @Test
    void handlesEmpty() {
        assertEquals("", TemplateEngine.render("", Map.of()));
    }
}
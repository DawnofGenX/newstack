package {{ package_name }};

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

class ConfigLoaderTest {
    @TempDir
    Path tmp;

    @Test
    void readsPropertiesFile() throws IOException {
        Path f = tmp.resolve("app.properties");
        Files.writeString(f, "db.host=localhost\ndb.port=5432\n");
        ConfigLoader cfg = new ConfigLoader(f, Map.of());
        assertEquals("localhost", cfg.get("db.host"));
        assertEquals(5432, cfg.getInt("db.port", 0));
    }

    @Test
    void defaultFallback() throws IOException {
        Path f = tmp.resolve("app.properties");
        Files.writeString(f, "");
        ConfigLoader cfg = new ConfigLoader(f, Map.of());
        assertEquals("fallback", cfg.get("missing", "fallback"));
        assertEquals(7, cfg.getInt("missing", 7));
        assertTrue(cfg.getBool("missing", true));
    }

    @Test
    void envOverridesFile() throws IOException {
        Path f = tmp.resolve("app.properties");
        Files.writeString(f, "db.host=filehost\n");
        Map<String, String> env = new HashMap<>();
        env.put("DB_HOST", "envhost");
        ConfigLoader cfg = new ConfigLoader(f, env);
        assertEquals("envhost", cfg.get("db.host"));
    }

    @Test
    void requiredThrowsWhenMissing() throws IOException {
        Path f = tmp.resolve("app.properties");
        Files.writeString(f, "");
        ConfigLoader cfg = new ConfigLoader(f, Map.of());
        assertThrows(IllegalStateException.class, () -> cfg.getRequired("nope"));
    }
}

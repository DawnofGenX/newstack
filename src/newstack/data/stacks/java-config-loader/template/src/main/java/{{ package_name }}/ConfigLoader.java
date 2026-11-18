package {{ package_name }};

import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;
import java.util.Properties;

public final class ConfigLoader {
    private final Properties props;
    private final Map<String, String> env;

    public ConfigLoader(Path path) throws IOException {
        this(path, System.getenv());
    }

    public ConfigLoader(Path path, Map<String, String> env) throws IOException {
        this.props = new Properties();
        try (InputStream in = Files.newInputStream(path)) {
            props.load(in);
        }
        this.env = env;
    }

    public ConfigLoader(Properties props, Map<String, String> env) {
        this.props = props;
        this.env = env;
    }

    public String get(String key) {
        return get(key, null);
    }

    public String get(String key, String defaultValue) {
        String envKey = key.toUpperCase().replace('.', '_').replace('-', '_');
        String v = env.get(envKey);
        if (v == null) {
            v = props.getProperty(key);
        }
        if (v == null) {
            v = defaultValue;
        }
        return v;
    }

    public int getInt(String key, int defaultValue) {
        String v = get(key);
        if (v == null) {
            return defaultValue;
        }
        return Integer.parseInt(v.trim());
    }

    public boolean getBool(String key, boolean defaultValue) {
        String v = get(key);
        if (v == null) {
            return defaultValue;
        }
        return Boolean.parseBoolean(v.trim());
    }

    public String getRequired(String key) {
        String v = get(key);
        if (v == null) {
            throw new IllegalStateException("missing required config key: " + key);
        }
        return v;
    }
}

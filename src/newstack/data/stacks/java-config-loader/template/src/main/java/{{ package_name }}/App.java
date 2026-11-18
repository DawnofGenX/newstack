package {{ package_name }};

import java.nio.file.Path;
import java.nio.file.Paths;

public final class App {
    private App() {}

    public static void main(String[] args) throws Exception {
        if (args.length < 2) {
            System.err.println("usage: config-loader <file> <key> [default]");
            System.exit(2);
            return;
        }
        Path path = Paths.get(args[0]);
        String key = args[1];
        String def = args.length > 2 ? args[2] : null;
        ConfigLoader cfg = new ConfigLoader(path);
        String value = cfg.get(key, def);
        if (value == null) {
            System.err.println("missing: " + key);
            System.exit(1);
            return;
        }
        System.out.println(value);
    }
}

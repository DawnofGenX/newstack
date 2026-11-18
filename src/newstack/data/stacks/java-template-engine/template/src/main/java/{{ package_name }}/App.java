package {{ package_name }};

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.HashMap;
import java.util.Map;

public class App {
    public static void main(String[] args) throws IOException {
        if (args.length < 1) {
            System.err.println("usage: template <file> [key=value ...]");
            System.exit(2);
        }
        String template = Files.readString(Paths.get(args[0]), StandardCharsets.UTF_8);
        Map<String, String> vars = new HashMap<>();
        for (int i = 1; i < args.length; i++) {
            int eq = args[i].indexOf('=');
            if (eq > 0) {
                vars.put(args[i].substring(0, eq), args[i].substring(eq + 1));
            }
        }
        System.out.print(TemplateEngine.render(template, vars));
    }
}
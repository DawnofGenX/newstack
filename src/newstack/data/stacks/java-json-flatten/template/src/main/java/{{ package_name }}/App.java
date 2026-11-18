package {{ package_name }};

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

public class App {
    public static void main(String[] args) throws IOException {
        ObjectMapper mapper = new ObjectMapper();
        String text;
        if (args.length > 0) {
            text = Files.readString(Paths.get(args[0]), StandardCharsets.UTF_8);
        } else {
            text = new String(System.in.readAllBytes(), StandardCharsets.UTF_8);
        }
        JsonNode root = mapper.readTree(text);
        ObjectNode flat = Flattener.flatten(root);
        System.out.println(mapper.writeValueAsString(flat));
    }
}

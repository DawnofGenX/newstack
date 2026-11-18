package {{ package_name }};

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;

public class App {
    public static void main(String[] args) throws IOException {
        String text;
        if (args.length > 0) {
            text = Files.readString(Paths.get(args[0]), StandardCharsets.UTF_8);
        } else {
            text = new String(System.in.readAllBytes(), StandardCharsets.UTF_8);
        }
        List<Person> people = CsvMapper.parse(text);
        for (Person p : people) {
            System.out.println(p.name() + "," + p.age() + "," + p.email());
        }
    }
}

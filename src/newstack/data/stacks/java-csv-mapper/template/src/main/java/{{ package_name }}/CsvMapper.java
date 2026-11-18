package {{ package_name }};

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public final class CsvMapper {
    private CsvMapper() {}

    public static List<Person> parse(String text) {
        if (text == null) {
            throw new IllegalArgumentException("missing input");
        }
        String[] lines = text.split("\\r?\\n", -1);
        if (lines.length == 0 || lines[0].trim().isEmpty()) {
            throw new IllegalArgumentException("missing header");
        }
        List<String> header = split(lines[0]);
        List<Person> out = new ArrayList<>();
        for (int i = 1; i < lines.length; i++) {
            if (lines[i].trim().isEmpty()) {
                continue;
            }
            List<String> row = split(lines[i]);
            if (row.size() != header.size()) {
                throw new IllegalArgumentException("bad column count");
            }
            out.add(map(header, row));
        }
        return out;
    }

    private static List<String> split(String line) {
        return new ArrayList<>(Arrays.asList(line.split(",", -1)));
    }

    private static Person map(List<String> header, List<String> row) {
        Map<String, Integer> index = new HashMap<>();
        for (int i = 0; i < header.size(); i++) {
            index.put(header.get(i).trim(), i);
        }
        if (!index.containsKey("name") || !index.containsKey("age") || !index.containsKey("email")) {
            throw new IllegalArgumentException("missing header");
        }
        String name = row.get(index.get("name")).trim();
        int age;
        try {
            age = Integer.parseInt(row.get(index.get("age")).trim());
        } catch (NumberFormatException e) {
            throw new IllegalArgumentException("wrong type", e);
        }
        String email = row.get(index.get("email")).trim();
        return new Person(name, age, email);
    }
}

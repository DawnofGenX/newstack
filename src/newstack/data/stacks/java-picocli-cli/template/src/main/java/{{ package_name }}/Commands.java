package {{ package_name }};

/** Small, easily testable command helpers. */
public final class Commands {

    private Commands() {}

    public static String greet(String name) {
        String who = (name == null || name.isBlank()) ? "world" : name.trim();
        return "Hello, " + who + "!";
    }

    public static int add(int a, int b) {
        return a + b;
    }
}
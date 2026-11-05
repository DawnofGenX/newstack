package {{ package_name }};

/** Entry point: {@code java -cp build/classes textstat.App}. */
public final class App {

    private App() {
    }

    /** Starts the service on HOST/PORT, defaulting to 127.0.0.1:8080. */
    public static void main(String[] args) throws Exception {
        String host = System.getenv().getOrDefault("HOST", "127.0.0.1");
        String raw = System.getenv().getOrDefault("PORT", "8080");
        int port;
        try {
            port = Integer.parseInt(raw);
        } catch (NumberFormatException error) {
            System.err.println("PORT must be a number, got " + raw);
            System.exit(2);
            return;
        }
        Server.serve(host, port);
    }
}

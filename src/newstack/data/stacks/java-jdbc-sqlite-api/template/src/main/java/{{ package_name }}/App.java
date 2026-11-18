package {{ package_name }};

import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.Executors;

public class App {
    public static void main(String[] args) throws Exception {
        int port = 5553;
        String database = "notes.db";
        for (int i = 0; i < args.length; i++) {
            if ("--port".equals(args[i]) && i + 1 < args.length) {
                port = Integer.parseInt(args[++i]);
            } else if ("--db".equals(args[i]) && i + 1 < args.length) {
                database = args[++i];
            }
        }

        NotesStore store = new NotesStore("jdbc:sqlite:" + database);
        HttpServer server = HttpServer.create(new InetSocketAddress(port), 0);
        server.createContext("/health", exchange -> handleHealth(exchange));
        server.createContext("/notes", exchange -> handleNotes(exchange, store));
        server.setExecutor(Executors.newFixedThreadPool(8));
        server.start();
        System.out.println("listening on " + port);
        Thread.currentThread().join();
    }

    private static void handleHealth(HttpExchange exchange) throws IOException {
        if (!"GET".equalsIgnoreCase(exchange.getRequestMethod())) {
            respond(exchange, 405, "method not allowed", "text/plain; charset=utf-8");
            return;
        }
        respond(exchange, 200, "ok", "text/plain; charset=utf-8");
    }

    private static void handleNotes(HttpExchange exchange, NotesStore store) throws IOException {
        String method = exchange.getRequestMethod();
        String path = exchange.getRequestURI().getPath();
        if ("GET".equalsIgnoreCase(method)) {
            respond(exchange, 200, Json.toJson(store.list()), "application/json; charset=utf-8");
            return;
        }
        if ("POST".equalsIgnoreCase(method)) {
            String body = readBody(exchange);
            String title = Json.field(body, "title");
            String noteBody = Json.field(body, "body");
            if (title == null || title.isBlank()) {
                respond(exchange, 400, "{\"error\":\"title is required\"}", "application/json; charset=utf-8");
                return;
            }
            if (noteBody == null) {
                noteBody = "";
            }
            store.add(title, noteBody);
            respond(exchange, 201, Json.toJson(new Note(title, noteBody)), "application/json; charset=utf-8");
            return;
        }
        if ("DELETE".equalsIgnoreCase(method)) {
            String title = null;
            if (path.length() > "/notes/".length()) {
                title = URLDecoder.decode(path.substring("/notes/".length()), StandardCharsets.UTF_8);
            } else {
                title = Json.queryParam(exchange.getRequestURI().getQuery(), "title");
            }
            if (title == null || title.isBlank()) {
                respond(exchange, 400, "{\"error\":\"title is required\"}", "application/json; charset=utf-8");
                return;
            }
            boolean removed = store.delete(title);
            respond(exchange, removed ? 200 : 404,
                    removed ? "{\"deleted\":true}" : "{\"deleted\":false}",
                    "application/json; charset=utf-8");
            return;
        }
        respond(exchange, 405, "method not allowed", "text/plain; charset=utf-8");
    }

    private static String readBody(HttpExchange exchange) throws IOException {
        try (InputStream input = exchange.getRequestBody()) {
            return new String(input.readAllBytes(), StandardCharsets.UTF_8);
        }
    }

    private static void respond(HttpExchange exchange, int status, String body, String contentType) throws IOException {
        byte[] bytes = body.getBytes(StandardCharsets.UTF_8);
        exchange.getResponseHeaders().set("Content-Type", contentType);
        exchange.sendResponseHeaders(status, bytes.length);
        try (OutputStream output = exchange.getResponseBody()) {
            output.write(bytes);
        }
    }
}
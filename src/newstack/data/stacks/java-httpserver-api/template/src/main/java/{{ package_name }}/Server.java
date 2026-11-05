package {{ package_name }};

import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.Executors;

/** The socket loop: {@code com.sun.net.httpserver} is part of the JDK, so no dependencies. */
public final class Server {

    private static final int MAX_BODY = 65536;

    private Server() {
    }

    /** Binds and serves until the process is stopped. */
    public static void serve(String host, int port) throws IOException {
        HttpServer server = HttpServer.create(new InetSocketAddress(host, port), 16);
        server.createContext("/", Server::handle);
        server.setExecutor(Executors.newFixedThreadPool(4));
        server.start();
        System.out.println("listening on http://" + host + ":" + port);
        System.out.flush();
    }

    private static void handle(HttpExchange exchange) throws IOException {
        try {
            String method = exchange.getRequestMethod();
            String target = exchange.getRequestURI().getRawPath();
            String query = exchange.getRequestURI().getRawQuery();
            String body = readBody(exchange.getRequestBody());
            Contract.Reply reply;
            if (body == null) {
                reply = Contract.error(413, "body_too_large", null);
            } else {
                reply = Contract.route(method, target, query, body);
            }
            byte[] payload = reply.body().getBytes(StandardCharsets.UTF_8);
            exchange.getResponseHeaders().set("content-type", "application/json");
            exchange.sendResponseHeaders(reply.status(), payload.length);
            try (OutputStream out = exchange.getResponseBody()) {
                out.write(payload);
            }
        } finally {
            exchange.close();
        }
    }

    private static String readBody(InputStream in) throws IOException {
        byte[] buffer = in.readNBytes(MAX_BODY + 1);
        if (buffer.length > MAX_BODY) {
            return null;
        }
        return new String(buffer, StandardCharsets.UTF_8);
    }
}

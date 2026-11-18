package {{ package_name }};

import com.sun.net.httpserver.HttpServer;
import org.junit.jupiter.api.Test;

import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class HttpClientApiTest {
    private static HttpServer start() throws Exception {
        HttpServer server = HttpServer.create(new InetSocketAddress(0), 0);
        server.createContext("/get", ex -> {
            byte[] body = "hello".getBytes(StandardCharsets.UTF_8);
            ex.sendResponseHeaders(200, body.length);
            ex.getResponseBody().write(body);
            ex.close();
        });
        server.createContext("/post", ex -> {
            byte[] in = ex.getRequestBody().readAllBytes();
            byte[] body = ("echo:" + new String(in, StandardCharsets.UTF_8)).getBytes(StandardCharsets.UTF_8);
            ex.sendResponseHeaders(201, body.length);
            ex.getResponseBody().write(body);
            ex.close();
        });
        server.start();
        return server;
    }

    @Test
    void getReturnsStatusAndBody() throws Exception {
        HttpServer server = start();
        try {
            String base = "http://localhost:" + server.getAddress().getPort();
            HttpClientApi client = new HttpClientApi();
            HttpClientApi.Response res = client.get(base + "/get");
            assertEquals(200, res.status());
            assertEquals("hello", res.body());
        } finally {
            server.stop(0);
        }
    }

    @Test
    void postSendsBody() throws Exception {
        HttpServer server = start();
        try {
            String base = "http://localhost:" + server.getAddress().getPort();
            HttpClientApi client = new HttpClientApi();
            HttpClientApi.Response res = client.post(base + "/post", "{\"x\":1}", "application/json");
            assertEquals(201, res.status());
            assertEquals("echo:{\"x\":1}", res.body());
        } finally {
            server.stop(0);
        }
    }
}
package {{ package_name }};

// java-http-client-api

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;

public final class HttpClientApi {
    // java-http-client-api
    private final HttpClient client;

    public HttpClientApi() {
        this.client = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(10))
                .build();
    }

    public record Response(int status, String body) {}

    public Response get(String url) throws IOException, InterruptedException {
        HttpRequest req = HttpRequest.newBuilder(URI.create(url))
                .GET()
                .timeout(Duration.ofSeconds(30))
                .build();
        HttpResponse<String> res = client.send(req, HttpResponse.BodyHandlers.ofString());
        return new Response(res.statusCode(), res.body());
    }

    public Response post(String url, String body, String contentType) throws IOException, InterruptedException {
        HttpRequest req = HttpRequest.newBuilder(URI.create(url))
                .header("Content-Type", contentType == null ? "application/json" : contentType)
                .POST(HttpRequest.BodyPublishers.ofString(body == null ? "" : body))
                .timeout(Duration.ofSeconds(30))
                .build();
        HttpResponse<String> res = client.send(req, HttpResponse.BodyHandlers.ofString());
        return new Response(res.statusCode(), res.body());
    }
}
package {{ package_name }};

import java.io.IOException;

public class App {
    public static void main(String[] args) throws Exception {
        HttpClientApi client = new HttpClientApi();
        if (args.length == 0) {
            System.err.println("usage: " + "{{ npm_name }}" + " <url> [post-body]");
            System.exit(2);
        }
        String url = args[0];
        HttpClientApi.Response res;
        if (args.length >= 2) {
            res = client.post(url, args[1], "application/json");
        } else {
            res = client.get(url);
        }
        System.out.println(res.status());
        System.out.println(res.body());
    }
}
package {{ package_name }};

public class App {
    public static void main(String[] args) {
        RateLimiter rl = new RateLimiter(3, 1, new SystemClock());
        for (int i = 0; i < 6; i++) {
            System.out.println("acquire " + i + ": " + rl.tryAcquire());
        }
    }
}

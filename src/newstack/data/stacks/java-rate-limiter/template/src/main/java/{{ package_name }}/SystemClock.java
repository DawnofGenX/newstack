package {{ package_name }};

public class SystemClock implements Clock {
    public long nowMillis() {
        return System.currentTimeMillis();
    }
}

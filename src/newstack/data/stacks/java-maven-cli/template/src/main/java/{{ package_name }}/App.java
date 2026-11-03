package {{ package_name }};

import java.io.InputStream;
import java.io.PrintStream;

/** Entry point: a thin wrapper that owns {@code System.exit}. */
public final class App {

    private App() {
        // not instantiable
    }

    public static void main(String[] args) {
        System.exit(start(args, System.in, System.out, System.err));
    }

    /** Same as {@link #main} but returns the code instead of exiting. */
    static int start(String[] args, InputStream stdin, PrintStream out, PrintStream err) {
        return new Cli(stdin).run(args, out, err);
    }
}

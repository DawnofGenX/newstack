package {{ package_name }};

import picocli.CommandLine;
import picocli.CommandLine.Command;
import picocli.CommandLine.Parameters;

@Command(
    name = "{{ npm_name }}",
    mixinStandardHelpOptions = true,
    version = "0.1.0",
    description = "{{ description }}",
    subcommands = { App.Greet.class, App.Add.class })
public final class App implements Runnable {

    private App() {}

    public static void main(String[] args) {
        System.exit(new CommandLine(new App()).execute(args));
    }

    @Override
    public void run() {
        CommandLine.usage(this, System.out);
    }

    @Command(name = "greet", description = "greet someone")
    public static final class Greet implements Runnable {
        @Parameters(paramLabel = "NAME", defaultValue = "world", description = "who to greet")
        private String name;

        @Override
        public void run() {
            System.out.println(Commands.greet(name));
        }
    }

    @Command(name = "add", description = "add two numbers")
    public static final class Add implements Runnable {
        @Parameters(index = "0", paramLabel = "A", description = "first number")
        private int a;

        @Parameters(index = "1", paramLabel = "B", description = "second number")
        private int b;

        @Override
        public void run() {
            System.out.println(Commands.add(a, b));
        }
    }
}
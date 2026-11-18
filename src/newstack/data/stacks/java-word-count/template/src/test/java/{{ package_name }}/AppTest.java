package {{ package_name }};

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.PrintWriter;
import java.io.StringReader;
import java.io.StringWriter;
import org.junit.jupiter.api.Test;

class AppTest {

    private record Result(int code, String out, String err) {
    }

    private static Result invoke(String arguments, String input) {
        StringWriter out = new StringWriter();
        StringWriter err = new StringWriter();
        String[] argv = arguments.isEmpty() ? new String[0] : arguments.split(" ");
        int code = App.run(argv, new StringReader(input), new PrintWriter(out, true), new PrintWriter(err, true));
        return new Result(code, out.toString(), err.toString());
    }

    @Test
    void printsTheTopWords() {
        Result result = invoke("--top 2", "a b b c c c");
        assertEquals(0, result.code());
        assertEquals("c 3\nb 2\n", result.out());
    }

    @Test
    void printsASingleWordCountWhenAsked() {
        Result result = invoke("--word The", "the cat and the hat");
        assertEquals(0, result.code());
        assertEquals("The 2\n", result.out());
    }

    @Test
    void allPrintsEveryWord() {
        Result result = invoke("--all", "one two two");
        assertEquals(0, result.code());
        assertEquals("two 2\none 1\n", result.out());
    }

    @Test
    void helpWinsWithExitZero() {
        Result result = invoke("--help", "");
        assertEquals(0, result.code());
        assertTrue(result.out().contains("Usage:"));
    }

    @Test
    void unknownOptionExitsTwo() {
        Result result = invoke("--bogus", "text");
        assertEquals(2, result.code());
        assertTrue(result.err().contains("unknown option --bogus"));
    }

    @Test
    void badTopExitsTwo() {
        assertEquals(2, invoke("--top", "x y").code());
        assertEquals(2, invoke("--top 0", "x").code());
        assertEquals(2, invoke("--top", "").code());
    }

    @Test
    void emptyInputPrintsNothing() {
        Result result = invoke("", "   ");
        assertEquals(0, result.code());
        assertEquals("", result.out());
    }
}

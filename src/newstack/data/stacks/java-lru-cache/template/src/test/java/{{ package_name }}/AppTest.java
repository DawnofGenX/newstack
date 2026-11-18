package {{ package_name }};

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.PrintWriter;
import java.io.StringReader;
import java.io.StringWriter;

import org.junit.jupiter.api.Test;

class AppTest {

    private record Result(int status, String out, String err) {
    }

    private static Result run(String[] args, String input) {
        StringWriter out = new StringWriter();
        StringWriter err = new StringWriter();
        int status = App.run(args, new StringReader(input), new PrintWriter(out, true),
                new PrintWriter(err, true));
        return new Result(status, out.toString(), err.toString());
    }

    @Test
    void traceProducesHitAndMissLines() {
        Result result = run(new String[] {"-c", "2"}, "PUT a 1\nGET a\nGET b\n");
        assertEquals(0, result.status());
        assertTrue(result.out().contains("GET a -> 1 (hit)"), result.out());
        assertTrue(result.out().contains("GET b -> miss"), result.out());
    }

    @Test
    void evictionIsReportedOnThePutLine() {
        Result result = run(new String[] {"-c", "1"}, "PUT a 1\nPUT b 2\n");
        assertEquals(0, result.status());
        assertTrue(result.out().contains("PUT b size=1 evicted=a"), result.out());
    }

    @Test
    void helpExitsZero() {
        Result result = run(new String[] {"--help"}, "");
        assertEquals(0, result.status());
        assertTrue(result.out().contains("usage: "));
    }

    @Test
    void unknownOptionExitsTwo() {
        assertEquals(2, run(new String[] {"--bogus"}, "").status());
    }

    @Test
    void zeroCapacityIsRejected() {
        Result result = run(new String[] {"-c", "0"}, "");
        assertEquals(2, result.status());
        assertTrue(result.err().contains("capacity must be at least 1"));
    }

    @Test
    void unknownCommandExitsOne() {
        Result result = run(new String[] {}, "FROB a\n");
        assertEquals(1, result.status());
        assertTrue(result.err().contains("unknown command: FROB"), result.err());
    }
}

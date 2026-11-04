/** A tally and two buffers. No framework: assertions and one report line. */
class Harness {
    static long passed = 0
    static long failed = 0
    static List<String> outBuffer = []
    static List<String> errBuffer = []

    static void resetAll() {
        passed = 0
        failed = 0
        outBuffer = []
        errBuffer = []
    }

    static void clearBuffers() {
        outBuffer = []
        errBuffer = []
    }

    static void out(String text) {
        outBuffer << text
    }

    static void err(String text) {
        errBuffer << text
    }

    static String outText() {
        return outBuffer.join('')
    }

    static String errText() {
        return errBuffer.join('')
    }

    static void check(String name, boolean ok, String detail = '') {
        if (ok) {
            passed += 1
        } else {
            failed += 1
            System.err.println("FAIL ${name}${detail ? ' (' + detail + ')' : ''}")
        }
    }

    static void checkEqual(String name, Object actual, Object expected) {
        check(name, actual == expected, "got ${actual}, want ${expected}")
    }

    static void checkText(String name, String actual, String expected) {
        check(name, actual == expected, "got ${actual.inspect()}, want ${expected.inspect()}")
    }

    static int report() {
        long total = passed + failed
        System.out.println("checks: ${total}, passed: ${passed}, failed: ${failed}")
        return failed == 0 ? 0 : 1
    }
}

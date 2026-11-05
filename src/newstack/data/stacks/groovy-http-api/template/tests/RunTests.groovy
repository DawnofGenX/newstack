// A stdlib-only test run: no Spock, no JUnit, no dependency to download.
//
// Every check records a name and a boolean; the script prints the tally and
// exits non-zero if anything failed, so `groovy tests/runTests.groovy` is a gate.

package textstat

class RunTests {
    static int passed = 0
    static int failed = 0

    static void check(String name, boolean condition) {
        if (condition) {
            passed++
        } else {
            failed++
            System.err.println("FAIL ${name}")
        }
    }

    static void checkEquals(String name, Object expected, Object actual) {
        check(name, expected == actual)
    }

    static void main(String[] args) {
        counts()
        json()
        contract()
        println "checks: ${passed + failed}, passed: ${passed}, failed: ${failed}".toString()
        if (failed > 0) {
            System.exit(1)
        }
    }

    static void counts() {
        check('empty', Counts.of('').lines == 0 && Counts.of('').words == 0 && Counts.of('').bytes == 0)
        check('one line', Counts.of('hello world\n').lines == 1)
        check('two words', Counts.of('hello world\n').words == 2)
        check('twelve bytes', Counts.of('hello world\n').bytes == 12)
        check('two lines', Counts.of('one two\nthree\n').lines == 2)
        check('three words', Counts.of('one two\nthree\n').words == 3)
        check('blank lines', Counts.of('\n\nx\n').lines == 3 && Counts.of('\n\nx\n').words == 1)
        check('spaces only', Counts.of('  \t ').words == 0 && Counts.of('  \t ').bytes == 4)
        check('no newline', Counts.of('abc').lines == 0 && Counts.of('abc').words == 1)
        // 12 characters, 14 UTF-8 bytes.
        check('utf8 bytes', Counts.of('héllo wörld\n').bytes == 14)
        check('utf8 words', Counts.of('héllo wörld\n').words == 2)
        check('emoji bytes', Counts.of('\uD83D\uDE42\n'.toString()).bytes == 5)
    }

    static void json() {
        check('plain string', Json.readText('{"text": "a b\\nc\\n"}').kind == Json.Kind.TEXT)
        check('string value kept', Json.readText('{"text": "a b\\nc\\n"}').text == 'a b\nc\n')
        check('number is missing', Json.readText('{"text": 42}').kind == Json.Kind.MISSING)
        check('string number is text', Json.readText('{"text": "42"}').kind == Json.Kind.TEXT)
        check('no key', Json.readText('{}').kind == Json.Kind.MISSING)
        check('not json', Json.readText('nope').kind == Json.Kind.INVALID)
        check('empty body', Json.readText('').kind == Json.Kind.INVALID)
        check('array body', Json.readText('["text"]').kind == Json.Kind.INVALID)
        check('unicode escape', Json.readText('{"text": "a\\u00e9"}').text == 'aé')
        check('surrogate pair', Json.readText('{"text": "\\ud83d\\ude42"}').text == '\uD83D\uDE42'.toString())
    }

    static void contract() {
        Reply health = Contract.route('GET', '/health', '', '')
        check('health status', health.status == 200)
        checkEquals('health body', '{"status":"ok"}', health.body)

        Reply get = Contract.route('GET', '/stats', 'text=hello%20world%0A', '')
        checkEquals('get body', '{"text":"hello world\\n","lines":1,"words":2,"bytes":12}', get.body)

        Reply post = Contract.route('POST', '/stats', '', '{"text": "a b\\nc\\n"}')
        checkEquals('post body', '{"text":"a b\\nc\\n","lines":2,"words":3,"bytes":6}', post.body)

        check('empty text', Contract.route('GET', '/stats', 'text=', '').body == '{"text":"","lines":0,"words":0,"bytes":0}')
        check('missing query', Contract.route('GET', '/stats', '', '').status == 422)
        check('missing field', Contract.route('POST', '/stats', '', '{}').status == 422)
        check('broken body', Contract.route('POST', '/stats', '', 'nope').status == 422)
        check('number field', Contract.route('POST', '/stats', '', '{"text": 42}').status == 422)
        check('wrong method on health', Contract.route('DELETE', '/health', '', '').status == 405)
        check('wrong method on stats', Contract.route('PUT', '/stats', 'text=a', '').status == 405)
        Reply missing = Contract.route('GET', '/nope', '', '')
        check('unknown route', missing.status == 404)
        checkEquals('unknown route body', '{"error":"not_found","detail":"no route for GET /nope"}', missing.body)
        check('second param', Contract.route('GET', '/stats', 'other=1&text=hi', '').body == '{"text":"hi","lines":0,"words":1,"bytes":2}')
        check('plus is space', Contract.route('GET', '/stats', 'text=a+b', '').body == '{"text":"a b","lines":0,"words":2,"bytes":3}')
    }
}

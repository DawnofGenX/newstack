
use Harness;
use Base32;

sub bytes(Str $text --> Buf) { $text.encode('utf-8').Buf }

sub encode-suite() {
    check-equal 'empty', base32-encode(Buf.new), '';
    check-equal 'hello', base32-encode(bytes('Hello')), 'JBSWY3DP';
    check-equal 'padding 1', base32-encode(bytes('a')), 'ME======';
    check-equal 'padding 2', base32-encode(bytes('ab')), 'MFRA====';
    check-equal 'padding 3', base32-encode(bytes('abc')), 'MFRGG===';
    check-equal 'padding 4', base32-encode(bytes('abcd')), 'MFRGGZA=';
    check-equal 'roundtrip', base32-decode-text(base32-encode-text('Hello World')), 'Hello World';
}

encode-suite();
exit report();

# A tally and two buffers. No framework: assertions and a report.
unit module Harness;

our $passed = 0;
our $failed = 0;
our @out-buffer;
our @err-buffer;

sub reset-all() is export {
    $passed = 0;
    $failed = 0;
    @out-buffer = ();
    @err-buffer = ();
}

sub clear-buffers() is export {
    @out-buffer = ();
    @err-buffer = ();
}

sub collect-out(Str $text) is export {
    @out-buffer.push($text);
    return True;
}

sub collect-err(Str $text) is export {
    @err-buffer.push($text);
    return True;
}

sub out-text(--> Str) is export { @out-buffer.join('') }
sub err-text(--> Str) is export { @err-buffer.join('') }

sub check(Str $name, Bool $ok, Str $detail = '') is export {
    if $ok {
        $passed += 1;
    }
    else {
        $failed += 1;
        note 'FAIL ' ~ $name ~ ($detail ?? ' (' ~ $detail ~ ')' !! '');
    }
}

# An Array and a List of the same values are the same answer.
sub same($actual, $expected --> Bool) {
    return $actual.Array eqv $expected.Array
        if $actual ~~ Positional and $expected ~~ Positional;
    return $actual eqv $expected;
}

sub check-equal(Str $name, $actual, $expected) is export {
    check($name, same($actual, $expected), 'got ' ~ $actual.raku ~ ', want ' ~ $expected.raku);
}

sub check-text(Str $name, Str $actual, Str $expected) is export {
    check($name, $actual eq $expected, 'got ' ~ $actual.raku ~ ', want ' ~ $expected.raku);
}

sub report(--> Int) is export {
    "checks: {$passed + $failed}, passed: $passed, failed: $failed\n".print;
    return $failed == 0 ?? 0 !! 1;
}

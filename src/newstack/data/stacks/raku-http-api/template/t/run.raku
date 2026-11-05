#!/usr/bin/env raku
# The gate: `raku -Ilib t/run.raku`. Rakudo's Test module is part of the core
# distribution, so this needs no install either.
use Test;
use Counts;
use Json;
use Contract;

my $hello = count-text("hello world\n");
is $hello<lines>, 1, 'one line for one newline';
is $hello<words>, 2, 'two words';
is $hello<bytes>, 12, 'twelve bytes';

my $empty = count-text('');
is $empty<lines>, 0, 'empty text has no lines';
is $empty<words>, 0, 'empty text has no words';
is $empty<bytes>, 0, 'empty text has no bytes';

my $blanks = count-text("\n\nx\n");
is $blanks<lines>, 3, 'blank lines still count';
is $blanks<words>, 1, 'one word around the blanks';

my $spaces = count-text("  \t ");
is $spaces<words>, 0, 'spaces and tabs are not words';
is $spaces<bytes>, 4, 'whitespace still counts as bytes';

is count-text('abc')<lines>, 0, 'no trailing newline means no line';
is count-text('abc')<words>, 1, 'a bare word still counts';

my $utf8 = count-text("héllo wörld\n");
is $utf8<words>, 2, 'two words in UTF-8';
is $utf8<bytes>, 14, 'UTF-8 bytes, not characters';

is count-text("🙂\n")<bytes>, 5, 'an emoji is four bytes plus the newline';
is count-text("a\x[0b]b\x[0c]c\n")<words>, 3, 'vertical tab and form feed separate words';

my %health = route('GET', '/health', '', '');
is %health<status>, 200, 'health is 200';
is %health<body>, '{"status":"ok"}', 'health body';

my %get = route('GET', '/stats', 'text=hello%20world%0A', '');
is %get<status>, 200, 'GET stats is 200';
is %get<body>, '{"text":"hello world\n","lines":1,"words":2,"bytes":12}', 'GET stats body';

my %question = route('GET', '/stats', '?text=a%20b%0Ac%0A', '');
is %question<body>, '{"text":"a b\nc\n","lines":2,"words":3,"bytes":6}', 'a leading ? is dropped';

my %plus = route('GET', '/stats', 'text=a+b%0A', '');
is %plus<body>, '{"text":"a b\n","lines":1,"words":2,"bytes":4}', 'a plus is a space';

is route('GET', '/stats', 'text=', '')<body>, '{"text":"","lines":0,"words":0,"bytes":0}', 'an empty value counts';

is route('GET', '/stats', '', '')<status>, 422, 'no query is 422';
is route('GET', '/stats', '', '')<body>, '{"error":"missing_text"}', 'no query body';
is route('GET', '/stats', 'other=1', '')<status>, 422, 'a missing text parameter is 422';

my %post = route('POST', '/stats', '', '{"text": "a b\nc\n"}');
is %post<status>, 200, 'POST stats is 200';
is %post<body>, '{"text":"a b\nc\n","lines":2,"words":3,"bytes":6}', 'POST stats body';

is route('POST', '/stats', '', '{"text": "  padded  \n"}')<body>,
    '{"text":"  padded  \n","lines":1,"words":1,"bytes":11}', 'nothing is trimmed';

is route('POST', '/stats', '', '{}')<body>, '{"error":"missing_text"}', 'no text member is 422';
is route('POST', '/stats', '', '{"text": 42}')<body>, '{"error":"missing_text"}', 'a number is not text';
is route('POST', '/stats', '', '{"meta": {"text": "x"}}')<body>,
    '{"error":"missing_text"}', 'a nested text is not the text';

is route('POST', '/stats', '', 'nope')<body>, '{"error":"invalid_json"}', 'a non-JSON body is invalid';
is route('POST', '/stats', '', '{"text": "a"} tail')<body>,
    '{"error":"invalid_json"}', 'trailing data is invalid';
is route('POST', '/stats', '', '[1, 2]')<body>, '{"error":"invalid_json"}', 'an array body is invalid';
is route('POST', '/stats', '', '42')<body>, '{"error":"invalid_json"}', 'a bare literal is invalid';
is route('POST', '/stats', '', '')<body>, '{"error":"invalid_json"}', 'an empty body is invalid';

is route('POST', '/stats', '', '{"text": "h\u00e9llo w\u00f6rld\n"}')<body>,
    '{"text":"héllo wörld\n","lines":1,"words":2,"bytes":14}', 'a \u escape is one character';
is route('POST', '/stats', '', '{"text": "\ud83d\ude42\n"}')<body>,
    '{"text":"🙂\n","lines":1,"words":1,"bytes":5}', 'a surrogate pair is one character';

my %gone = route('GET', '/nope', '', '');
is %gone<status>, 404, 'an unknown path is 404';
is %gone<body>, '{"error":"not_found","detail":"no route for GET /nope"}', '404 names the route';

is route('DELETE', '/health', '', '')<status>, 405, 'a wrong method is 405';
is route('POST', '/health', '', '')<body>, '{"error":"method_not_allowed"}', '405 body';
is route('HEAD', '/stats', 'text=x', '')<status>, 405, 'HEAD is not routed';

is json-quote("a\"b\\c\n"), '"a\"b\\\\c\n"', 'json-quote escapes quotes, slashes and newlines';
is percent-decode('%C3%A9'), 'é', 'percent escapes are bytes, then UTF-8';
is read-body('{"text": "x"}')<kind>, 'text', 'the reader finds text';
is read-body('{"text": null}')<kind>, 'missing', 'a null text is not a string';

done-testing;

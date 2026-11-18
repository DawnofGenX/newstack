use strict;
use warnings;

use lib 'lib';

use Test::More;
use IniLite;
use IniLite::Parse;

my $text = <<'INI';
; leading comment
port = 8080
name = "my service"

[server]
host = localhost   # inline comment
tls = true

[db]
url = postgres://localhost/app
INI

my $doc = IniLite->parse_text($text);
isa_ok($doc, 'IniLite::Parse', 'parse_text returns a Parse object');
is_deeply([$doc->order], ['', 'server', 'db'], 'sections keep file order');

is($doc->get('', 'port'), '8080', 'a key before any section belongs to the unnamed section');
is($doc->get('', 'name'), 'my service', 'quotes are stripped from values');
is($doc->get('server', 'host'), 'localhost', 'an inline comment is not part of the value');
is($doc->get('server', 'tls'), 'true', 'bare booleans are plain strings');
is($doc->get('db', 'url'), 'postgres://localhost/app', 'a colon in the value is kept');
is($doc->get('server', 'missing'), undef, 'an unknown key is undef');
is($doc->has_section('db'), 1, 'has_section finds a section');
is($doc->has_section('nope'), '', 'has_section rejects an unknown section');

my @pairs = $doc->pairs('server');
is_deeply([map { $_->[0] } @pairs], ['host', 'tls'], 'pairs() keeps key order');

my ($value, $section, $key) = $doc->lookup('db.url');
is($value, 'postgres://localhost/app', 'lookup() resolves section.key');
is($section, 'db', 'lookup() returns the section it matched');
is($key, 'url', 'lookup() returns the key it matched');
is((($doc->lookup('port'))[0]), '8080', 'lookup() falls back to the unnamed section');

my $flat = $doc->flatten;
is($flat->{'server.host'}, 'localhost', 'flatten() qualifies section keys');
is($flat->{port}, '8080', 'flatten() leaves unnamed keys bare');

my $hashed = IniLite::Parse->parse("# only a comment\npass = a#b\n");
is($hashed->get('', 'pass'), 'a#b', 'a hash inside a value is data when not preceded by space');

my $quoted = IniLite::Parse->parse("path = \"a\\nb\"\n");
is($quoted->get('', 'path'), "a\nb", 'escapes inside quotes are resolved');

my $empty = IniLite::Parse->parse("[empty]\n");
is_deeply([$empty->order], ['empty'], 'an empty section is still a section');
is_deeply([$empty->pairs('empty')], [], 'an empty section has no pairs');

my $duplicate = IniLite::Parse->parse("a = 1\na = 2\n");
is($duplicate->get('', 'a'), '2', 'the last duplicate wins');
is_deeply([map { $_->[0] } $duplicate->pairs('')], ['a'], 'a duplicate is listed once');

my $ok = eval { IniLite::Parse->parse("this is not ini\n"); 1 };
is($ok, undef, 'a line with neither a section nor a key dies');
like($@, qr/line 1: expected \[section\] or key = value/, 'the error names the line');

is(IniLite->version, '0.01', 'the facade exposes the distribution version');

done_testing();

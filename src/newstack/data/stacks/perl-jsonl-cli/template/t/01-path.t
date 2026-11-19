use strict;
use warnings;

use Test::More;
use lib 'lib';

use Jsonl;

is_deeply([Jsonl::split_path('a.b')], ['a', 'b'], 'dotted path');
is_deeply([Jsonl::split_path('tags[0]')], ['tags', 0], 'indexed path');
is_deeply([Jsonl::split_path('a.b[2].c')], ['a', 'b', 2, 'c'], 'mixed path');
is_deeply([Jsonl::split_path('[0]')], [0], 'leading index');
is_deeply([Jsonl::split_path('.a')], ['a'], 'tolerates a leading dot');

eval { Jsonl::split_path('') };
like($@, qr/empty path/, 'empty path is refused');

eval { Jsonl::split_path('a..b') };
like($@, qr/malformed path 'a\.\.b'/, 'double dot is refused');

my $row = { id => 1, user => { name => 'ada' }, tags => ['math', 'logic'], empty => undef };

my ($found, $value) = Jsonl::fetch($row, 'user.name');
ok($found, 'nested key found');
is($value, 'ada', 'nested value');

is(Jsonl::value_at($row, 'tags[1]'), 'logic', 'array index');
is(Jsonl::value_at($row, 'tags[9]'), undef, 'index past the end');

my ($missing_found) = Jsonl::fetch($row, 'user.missing');
ok(!$missing_found, 'missing key reports not found');

my ($null_found, $null_value) = Jsonl::fetch($row, 'empty');
ok($null_found, 'a JSON null is present');
is($null_value, undef, '... and reads as undef');

my ($deep_found) = Jsonl::fetch($row, 'user.name.first');
ok(!$deep_found, 'walking through a scalar finds nothing');

is_deeply(
    Jsonl::pick($row, 'id', 'user.name', 'user.missing'),
    { id => 1, user => { name => 'ada' } },
    'pick keeps only the requested paths'
);

is_deeply(Jsonl::pick($row, 'tags'), { tags => ['math', 'logic'] }, 'pick keeps arrays whole');

ok(Jsonl::looks_numeric('10'), 'integer is numeric');
ok(Jsonl::looks_numeric('-9.5'), 'negative decimal is numeric');
ok(Jsonl::looks_numeric('1e3'), 'exponent is numeric');
ok(!Jsonl::looks_numeric('010'), 'leading zero is text');
ok(!Jsonl::looks_numeric('10px'), 'suffixed number is text');

is(Jsonl::text_of(undef), '', 'undef renders empty');
is(Jsonl::text_of({ a => 1 }), '{"a":1}', 'containers render as JSON');

done_testing();

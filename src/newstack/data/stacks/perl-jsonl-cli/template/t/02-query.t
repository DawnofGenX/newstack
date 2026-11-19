use strict;
use warnings;

use Test::More;
use lib 'lib';

use JSON::PP ();
use Jsonl;
use Jsonl::Query;
use Jsonl::Stats;

my $row = { id => 1, score => 10, name => 'ada', flag => JSON::PP::true, zero => 0 };

is(Jsonl::Query::compare('10', '9'), 1, 'numeric strings compare numerically');
is(Jsonl::Query::compare('abc', 'abd'), -1, 'text compares as text');
is(Jsonl::Query::compare('010', '9'), -1, 'a leading zero keeps the value in text order');
is(Jsonl::Query::compare('010', '9', 1), 1, '--numeric coerces the same pair to numbers');
is(Jsonl::Query::compare('bench', '9', 1), -1, '--numeric reads non-numeric text as 0');

# equality goes through the same comparison, so 10 equals "10"
my $clause = Jsonl::Query::parse_where(path => 'score', eq => '10');
ok(Jsonl::Query::matches($row, $clause), 'equals matches a number');

$clause = Jsonl::Query::parse_where(path => 'name', eq => 'bob');
ok(!Jsonl::Query::matches($row, $clause), 'equals rejects another value');

$clause = Jsonl::Query::parse_where(path => 'name', ne => 'bob');
ok(Jsonl::Query::matches($row, $clause), 'not-equals');

$clause = Jsonl::Query::parse_where(path => 'score', gt => '9');
ok(Jsonl::Query::matches($row, $clause), 'greater than');
$clause = Jsonl::Query::parse_where(path => 'score', gt => '10');
ok(!Jsonl::Query::matches($row, $clause), 'greater than is strict');
$clause = Jsonl::Query::parse_where(path => 'score', ge => '10');
ok(Jsonl::Query::matches($row, $clause), 'greater or equal');
$clause = Jsonl::Query::parse_where(path => 'score', lt => '11');
ok(Jsonl::Query::matches($row, $clause), 'less than');
$clause = Jsonl::Query::parse_where(path => 'score', le => '10');
ok(Jsonl::Query::matches($row, $clause), 'less or equal');

$clause = Jsonl::Query::parse_where(path => 'name', match => '^a');
ok(Jsonl::Query::matches($row, $clause), 'regex match');

$clause = Jsonl::Query::parse_where(path => 'name');
ok(Jsonl::Query::matches($row, $clause), 'bare --where is a truthiness test');
$clause = Jsonl::Query::parse_where(path => 'zero');
ok(!Jsonl::Query::matches($row, $clause), 'zero is falsy');
$clause = Jsonl::Query::parse_where(path => 'missing');
ok(!Jsonl::Query::matches($row, $clause), 'a missing key is falsy');
$clause = Jsonl::Query::parse_where(path => 'flag');
ok(Jsonl::Query::matches($row, $clause), 'true is truthy');

eval { Jsonl::Query::parse_where(path => 'score', gt => 'nine') };
like($@, qr/--gt needs a number/, 'numeric operators validate their value');

eval { Jsonl::Query::parse_where(path => 'score', eq => '1', ne => '2') };
like($@, qr/exactly one of/, 'only one comparison per clause');

eval { Jsonl::Query::parse_where(path => 'name', match => '(') };
like($@, qr/invalid regular expression/, 'broken regex is refused');

my $stats = Jsonl::Stats::numeric_stats(
    [ { n => 10 }, { n => 9.5 }, { n => 30 }, { n => 'not a number' }, { other => 1 } ],
    'n',
);
is($stats->{count}, 3, 'stats count numeric values only');
is($stats->{sum}, 49.5, 'stats sum');
is($stats->{mean}, 16.5, 'stats mean');
is($stats->{min}, 9.5, 'stats min');
is($stats->{max}, 30, 'stats max');

eval { Jsonl::Stats::numeric_stats([ { n => 'x' } ], 'n') };
like($@, qr/no numeric values at 'n'/, 'stats reports an empty column');

done_testing();

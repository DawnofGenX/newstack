use strict;
use warnings;
use lib 'lib';
use Test::More;
use CsvQuery::Parser;
use CsvQuery::Query;

my $rows = CsvQuery::Parser::parse_csv("a,b\n1,2\n3,4\n");
is(scalar @$rows, 3, 'row count');
is($rows->[0][0], 'a', 'header');

my $sel = CsvQuery::Query::select_columns($rows, 'b');
is($sel->[1][0], '2', 'select');

my $filt = CsvQuery::Query::filter_rows($rows, 'a', '3');
is(scalar @$filt, 2, 'filter');

is(CsvQuery::Query::sum_column($rows, 'b'), 6, 'sum');

# quoted fields
my $q = CsvQuery::Parser::parse_csv(qq{"a,b",c\n1,2\n});
is($q->[0][0], 'a,b', 'quoted comma');

done_testing();

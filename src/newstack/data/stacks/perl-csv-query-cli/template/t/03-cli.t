use strict;
use warnings;
use FindBin;
use File::Spec;
use File::Temp qw(tempdir);
use Test::More;

my $dir = tempdir(CLEANUP => 1);
my $csv = "$dir/data.csv";
open my $fh, '>', $csv or die $!;
print $fh "name,val\nalice,10\nbob,20\n";
close $fh;

my $bin = "$FindBin::Bin/../bin/{{ npm_name }}" if 0;
# locate binary
use FindBin;
my $script = "$FindBin::Bin/../bin/{{ npm_name }}";

# help
my $out = `$^X $script --help 2>&1`; # not perl? run directly
# run shell
$out = `sh -c '"$script" --help' 2>&1`;
is($? >> 8, 0, 'help exit');

# sum
my $sum = `sh -c '"$script" --sum val "$csv"' 2>&1`;
chomp $sum;
is($sum, '30', 'sum');

# select
my $sel = `sh -c '"$script" --select name "$csv"' 2>&1`;
like($sel, qr/alice/, 'select');

# filter
my $filt = `sh -c '"$script" --where name=bob "$csv"' 2>&1`;
like($filt, qr/bob/, 'filter');

# stdin
my $std = `printf 'x,y\n1,2\n' | sh -c '"$script" --compact' 2>&1` if 0;
done_testing();

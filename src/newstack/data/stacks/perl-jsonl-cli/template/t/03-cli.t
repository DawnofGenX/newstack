use strict;
use warnings;

use File::Spec;
use File::Temp qw(tempdir);
use Test::More;

# Exit codes only count when the real binary produced them.
my $script = File::Spec->catfile('bin', '{{ npm_name }}');
ok(-f $script, 'the executable entry point exists');

my $directory = tempdir(CLEANUP => 1);
my $data = File::Spec->catfile($directory, 'rows.jsonl');

open(my $handle, '>', $data) or die "cannot write $data: $!";
print {$handle} qq({"id":1,"user":{"name":"ada"},"score":10}\n);
print {$handle} qq({"id":2,"user":{"name":"bob"},"score":9.5}\n);
print {$handle} qq({"id":3,"user":{"name":"cy"},"score":30}\n);
close $handle;

sub run_cli {
    my (@args) = @_;

    my $pid = open(my $pipe, '-|');
    die "cannot fork: $!" unless defined $pid;
    if (!$pid) {
        open STDERR, '>&', \*STDOUT or die "cannot redirect stderr: $!";
        exec($^X, $script, @args);
        exit 127;
    }

    local $/;
    my $output = <$pipe>;
    close $pipe;
    my $status = $? >> 8;
    $output = '' unless defined $output;
    # chomp() is a no-op while $/ is undef, so drop the final newline by hand.
    $output =~ s/\n\z//;
    return ($status, $output);
}

my ($status, $output) = run_cli('--help');
is($status, 0, 'help exits 0');
like($output, qr/^usage: /m, 'help prints usage');

($status, $output) = run_cli('--version');
is($status, 0, 'version exits 0');
is($output, '0.01', 'version prints the module version');

($status, $output) = run_cli('--count', $data);
is($status, 0, 'count exits 0');
is($output, '3', 'count counts records');

($status, $output) = run_cli('--where', 'score', '--gt', '9.9', '--count', $data);
is($status, 0, 'filter exits 0');
is($output, '2', 'filter keeps the numeric matches');

($status, $output) = run_cli('--where', 'user.name', '--match', '^c', '--count', $data);
is($status, 0, 'regex filter exits 0');
is($output, '1', 'regex filter matches one record');

($status, $output) = run_cli('--sort', 'score', '--numeric', $data);
is($status, 0, 'sort exits 0');
my @lines = split /\n/, $output;
is(scalar @lines, 3, 'sort keeps every record');
like($lines[0], qr/"score":9\.5/, 'numeric sort puts 9.5 first');
like($lines[2], qr/"score":30/, 'numeric sort puts 30 last');

($status, $output) = run_cli('-f', 'id,user.name', $data);
is($status, 0, 'projection exits 0');
is($output, qq({"id":1,"user":{"name":"ada"}}\n{"id":2,"user":{"name":"bob"}}\n{"id":3,"user":{"name":"cy"}}), 'projection keeps only the requested paths');

($status, $output) = run_cli('--stats', 'score', $data);
is($status, 0, 'stats exits 0');
is($output, 'count=3 sum=49.5 mean=16.5 min=9.5 max=30', 'stats output');

($status, $output) = run_cli('--bogus');
is($status, 2, 'an unknown option exits 2');
like($output, qr/unknown option '--bogus'/, '... and names it');

($status, $output) = run_cli('--where', 'score', '--gt', 'nine', $data);
is($status, 2, 'a non-numeric --gt exits 2');

($status, $output) = run_cli('does-not-exist.jsonl');
is($status, 1, 'a missing file exits 1');
like($output, qr/cannot read does-not-exist\.jsonl/, '... and names the file');

my $broken = File::Spec->catfile($directory, 'broken.jsonl');
open($handle, '>', $broken) or die "cannot write $broken: $!";
print {$handle} qq({"a":1}\n);
print {$handle} "not json\n";
close $handle;

($status, $output) = run_cli($broken);
is($status, 1, 'broken json exits 1');
like($output, qr/line 2: not valid JSON/, '... and names the line');

my $array = File::Spec->catfile($directory, 'array.jsonl');
open($handle, '>', $array) or die "cannot write $array: $!";
print {$handle} "[1,2,3]\n";
close $handle;

($status, $output) = run_cli($array);
is($status, 1, 'a non-object record exits 1');
like($output, qr/line 1: expected a JSON object/, '... and says why');

($status, $output) = run_cli($data, $data);
is($status, 2, 'two files are a usage error');

done_testing();

use strict;
use warnings;

use File::Spec;
use File::Temp qw(tempdir);
use Test::More;

# Prove the exit codes with the real binary instead of calling into the library:
# `--help` is 0, bad usage is 2, an unreadable file is 1. Run from the
# distribution root, which is where `make test` puts us.
my $script = File::Spec->catfile('bin', '{{ npm_name }}');
ok(-f $script, 'the executable entry point exists');

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

    return ($? >> 8, defined $output ? $output : '');
}

my $workdir = tempdir(CLEANUP => 1);
my $sample = File::Spec->catfile($workdir, 'sample.txt');
open my $fh, '>:raw', $sample or die "cannot write $sample: $!";
print {$fh} "one two\nthree\n";
close $fh;

my ($status, $output) = run_cli('--help');
is($status, 0, '--help exits 0');
like($output, qr/usage: /, '--help prints a usage line');
like($output, qr/{{ npm_name }}/, 'the usage line names the real binary');
like($output, qr/-l, --lines/, 'help documents the modes');

($status, $output) = run_cli('--version');
is($status, 0, '--version exits 0');
like($output, qr/\A\d+\.\d+/, '--version prints a version');

($status, $output) = run_cli('--bogus');
is($status, 2, 'an unknown flag exits 2');
like($output, qr/unknown option '--bogus'/, 'the unknown flag is reported');
like($output, qr/usage: /, 'a usage error repeats the usage line');

($status, $output) = run_cli('-l', '-w');
is($status, 2, 'conflicting modes exit 2');

($status, $output) = run_cli(File::Spec->catfile($workdir, 'does-not-exist.txt'));
is($status, 1, 'an unreadable file exits 1');
like($output, qr/cannot open/, 'the unreadable file is named in the error');

($status, $output) = run_cli('-l', $sample);
is($status, 0, 'counting a file exits 0');
is($status == 0 && $output =~ /\s(\d+)\s+\Q$sample\E/, 1, 'a single figure is printed with the file name');
like($output, qr/\s2\s/, 'the line count is 2');

($status, $output) = run_cli('-w', $sample);
like($output, qr/\s3\s/, 'the word count is 3');

($status, $output) = run_cli('-c', $sample);
like($output, qr/\s14\s/, 'the byte count is 14');

($status, $output) = run_cli($sample);
is($status, 0, 'no flag still exits 0');
like($output, qr/\s2\s+\s3\s+\s14\s/, 'no flag prints lines, words and bytes in that order');

($status, $output) = run_cli($sample, $sample);
is($status, 0, 'two files exit 0');
like($output, qr/total/, 'two files print a total');

($status, $output) = run_cli('--', '-l');
is($status, 1, '-- makes -l a file name, which cannot be opened');
like($output, qr/cannot open '-l'/, 'the file name after -- is echoed verbatim');

done_testing();

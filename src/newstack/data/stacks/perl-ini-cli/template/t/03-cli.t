use strict;
use warnings;

use File::Spec;
use File::Temp qw(tempdir);
use Test::More;

# The exit codes only count when the real binary produced them.
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

sub write_sample {
    my ($path) = @_;

    open my $handle, '>:raw', $path or die "cannot write $path: $!";
    print {$handle} "; sample\nport = 8080\n\n[server]\nhost = localhost\n\n[db]\nurl = postgres://x\n";
    close $handle;
    return $path;
}

my $workdir = tempdir(CLEANUP => 1);
my $sample = write_sample(File::Spec->catfile($workdir, 'app.ini'));

my ($status, $output) = run_cli('--help');
is($status, 0, '--help exits 0');
like($output, qr/usage: /, '--help prints a usage line');
like($output, qr/{{ npm_name }}/, 'the usage line names the real binary');

($status, $output) = run_cli('--version');
is($status, 0, '--version exits 0');
like($output, qr/\A\d+\.\d+/, '--version prints a version');

($status, $output) = run_cli('--bogus');
is($status, 2, 'an unknown flag exits 2');
like($output, qr/unknown option/, 'the unknown flag is reported');

($status, $output) = run_cli(File::Spec->catfile($workdir, 'nope.ini'));
is($status, 1, 'a missing file exits 1');
like($output, qr/cannot open/, 'the missing file is named');

($status, $output) = run_cli($sample);
is($status, 0, 'printing a file exits 0');
like($output, qr/port = 8080/, 'the unnamed key is printed');
like($output, qr/\[server\]\nhost = localhost/, 'the section header is printed');

($status, $output) = run_cli('--list-sections', $sample);
is($status, 0, '--list-sections exits 0');
like($output, qr/\Aserver\ndb\n\z/, 'sections are listed in file order');

($status, $output) = run_cli('-s', 'server', $sample);
is($status, 0, '--section exits 0');
is($output, "[server]\nhost = localhost\n", 'only the requested section is printed');

($status, $output) = run_cli('-g', 'db.url', $sample);
is($status, 0, '--get exits 0');
is($output, "postgres://x\n", 'the requested value is printed alone');

($status, $output) = run_cli('-g', 'db.missing', $sample);
is($status, 2, 'an unknown key exits 2');
like($output, qr/no such key/, 'the unknown key is named');

($status, $output) = run_cli('-s', 'nope', $sample);
is($status, 2, 'an unknown section exits 2');

($status, $output) = run_cli('--json', $sample);
is($status, 0, '--json exits 0');
like($output, qr/"port":"8080"/, 'json keeps unnamed keys');
like($output, qr/"host":"localhost"/, 'json nests section keys');

my $broken = File::Spec->catfile($workdir, 'broken.ini');
open my $handle, '>:raw', $broken or die "cannot write $broken: $!";
print {$handle} "not ini\n";
close $handle;

($status, $output) = run_cli($broken);
is($status, 1, 'malformed input exits 1');
like($output, qr/line 1:/, 'the parse error names the line');

done_testing();

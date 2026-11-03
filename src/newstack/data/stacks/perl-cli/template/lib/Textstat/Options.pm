package Textstat::Options;

use strict;
use warnings;

# Hand-rolled argv parsing: every branch is a unit test, and nothing here
# prints or exits. parse() returns a hashref whose `status` tells the caller
# what to do next: run, show help, show the version, or complain and exit 2.

my %MODE_OF = (
    '-l'      => 'lines',
    '--lines' => 'lines',
    '-w'      => 'words',
    '--words' => 'words',
    '-c'      => 'bytes',
    '--bytes' => 'bytes',
);

sub version { return '0.01' }

sub parse {
    my (@argv) = @_;

    my $mode;
    my @files;
    my $status = 'ok';
    my $error;
    my $only_files = 0;

    for my $arg (@argv) {
        # After `--`, and for the two arguments that only look like flags,
        # everything is a file name.
        if ($only_files || $arg eq '' || $arg eq '-') {
            push @files, $arg;
            next;
        }

        if ($arg eq '--') {
            $only_files = 1;
            next;
        }

        if ($arg eq '-h' || $arg eq '--help') {
            $status = 'help';
            last;
        }

        if ($arg eq '-V' || $arg eq '--version') {
            $status = 'version';
            last;
        }

        if (my $candidate = $MODE_OF{$arg}) {
            if (defined $mode && $mode ne $candidate) {
                $error  = "$arg conflicts with an earlier mode";
                $status = 'error';
                last;
            }
            $mode = $candidate;
            next;
        }

        if ($arg =~ /\A-/) {
            $error  = "unknown option '$arg'";
            $status = 'error';
            last;
        }

        push @files, $arg;
    }

    return {
        status => $status,
        mode   => defined $mode ? $mode : 'all',
        files  => \@files,
        error  => $error,
    };
}

sub usage {
    my ($program) = @_;

    return <<"USAGE";
usage: $program [-l | -w | -c] [--] [FILE ...]

Count lines, words and bytes in each FILE, or in standard input
when no FILE is given. With more than one FILE a total is printed.

  -l, --lines     print the line count only
  -w, --words     print the word count only
  -c, --bytes     print the byte count only
  -h, --help      show this help and exit
  -V, --version   show the version and exit
USAGE
}

1;

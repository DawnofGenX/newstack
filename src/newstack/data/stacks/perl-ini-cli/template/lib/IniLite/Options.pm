package IniLite::Options;

use strict;
use warnings;

# Hand-rolled argv parsing: nothing here prints or exits. `status` tells the
# caller what to do next: run, help, version, or complain and exit 2.

sub version { return '0.01' }

sub parse {
    my (@argv) = @_;

    my %options = (
        section => undef,
        get     => undef,
        json    => 0,
        list    => 0,
        files   => [],
        status  => 'ok',
        error   => undef,
    );

    my $only_files = 0;
    my $index = 0;

    while ($index < @argv) {
        my $arg = $argv[$index];
        $index++;

        if ($only_files || $arg eq '' || $arg eq '-') {
            push @{ $options{files} }, $arg;
            next;
        }

        if ($arg eq '--') {
            $only_files = 1;
            next;
        }

        if ($arg eq '-h' || $arg eq '--help') {
            $options{status} = 'help';
            last;
        }

        if ($arg eq '-V' || $arg eq '--version') {
            $options{status} = 'version';
            last;
        }

        if ($arg eq '--json') {
            $options{json} = 1;
            next;
        }

        if ($arg eq '--list-sections') {
            $options{list} = 1;
            next;
        }

        if ($arg eq '-s' || $arg eq '--section') {
            if ($index >= @argv) {
                $options{status} = 'error';
                $options{error}  = "option '$arg' needs a value";
                last;
            }
            $options{section} = $argv[$index];
            $index++;
            next;
        }

        if ($arg =~ /\A--section=(.*)\z/) {
            $options{section} = $1;
            next;
        }

        if ($arg eq '-g' || $arg eq '--get') {
            if ($index >= @argv) {
                $options{status} = 'error';
                $options{error}  = "option '$arg' needs a value";
                last;
            }
            $options{get} = $argv[$index];
            $index++;
            next;
        }

        if ($arg =~ /\A--get=(.*)\z/) {
            $options{get} = $1;
            next;
        }

        if ($arg =~ /\A-/) {
            $options{status} = 'error';
            $options{error}  = "unknown option '$arg'";
            last;
        }

        push @{ $options{files} }, $arg;
    }

    return \%options;
}

sub usage {
    my ($program) = @_;

    return <<"USAGE";
usage: $program [options] [FILE]

Read an INI file from FILE (or standard input) and print it back, select a
section, look a value up, or emit the whole document as JSON.

  -s, --section NAME   print only the named section
  -g, --get PATH       print one value: "section.key", or "key" at the top
      --json           emit the document as a JSON object
      --list-sections  print the section names, one per line
  -h, --help           show this help and exit
  -V, --version        show the version and exit
USAGE
}

1;

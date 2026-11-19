package Jsonl::Options;

use strict;
use warnings;

our $VERSION = '0.01';

# Returns a hash with status => ok|help|version|error and either a command or
# an error message. Unknown options are caught here, never by the command.
sub parse {
    shift;    # the invocant: parse is always called as Jsonl::Options->parse(...)
    my (@argv) = @_;

    my %options = (
        status  => 'ok',
        command => undef,
        file    => undef,
        fields  => [],
        sort    => undef,
        numeric => 0,
        reverse => 0,
        count   => 0,
        compact => 0,
        where   => undef,
        stats   => undef,
    );

    my @args = @argv;
    my $literal = 0;

    while (@args) {
        my $argument = shift @args;

        if ($literal) {
            push @{$options{operands}}, $argument;
            next;
        }
        if ($argument eq '--') {
            $literal = 1;
            next;
        }
        if ($argument eq '-h' || $argument eq '--help') {
            $options{status} = 'help';
            return \%options;
        }
        if ($argument eq '-V' || $argument eq '--version') {
            $options{status} = 'version';
            return \%options;
        }
        if ($argument eq '-f' || $argument eq '--fields') {
            my $value = shift @args;
            return error(\%options, "$argument needs a value") unless defined $value;
            $options{fields} = [grep { length } split /,/, $value];
            next;
        }
        if ($argument eq '--sort') {
            my $value = shift @args;
            return error(\%options, '--sort needs a path') unless defined $value;
            $options{sort} = $value;
            next;
        }
        if ($argument eq '--stats') {
            my $value = shift @args;
            return error(\%options, '--stats needs a path') unless defined $value;
            $options{stats} = $value;
            next;
        }
        if ($argument eq '--where') {
            my $value = shift @args;
            return error(\%options, '--where needs a path') unless defined $value;
            $options{where} = $value;
            next;
        }
        if ($argument =~ /\A--(eq|ne|gt|ge|lt|le|match)\z/) {
            my $name = $1;
            my $value = shift @args;
            return error(\%options, "--$name needs a value") unless defined $value;
            return error(\%options, "--$name needs --where PATH") unless defined $options{where};
            return error(\%options, 'only one comparison per run') if defined $options{where_op};
            $options{where_op} = $name;
            $options{where_value} = $value;
            next;
        }
        if ($argument eq '--numeric') { $options{numeric} = 1; next }
        if ($argument eq '--reverse') { $options{reverse} = 1; next }
        if ($argument eq '--count')   { $options{count} = 1;   next }
        if ($argument eq '--compact') { $options{compact} = 1; next }
        if ($argument =~ /\A-./) {
            return error(\%options, "unknown option '$argument'");
        }
        if ($argument eq '-') {
            push @{$options{operands}}, $argument;
            next;
        }
        push @{$options{operands}}, $argument;
    }

    my @operands = @{$options{operands} || []};
    if (@operands > 1) {
        return error(\%options, sprintf('expected at most one file, got %d', scalar @operands));
    }
    $options{file} = $operands[0];

    return \%options;
}

sub error {
    my ($options, $message) = @_;
    $options->{status} = 'error';
    $options->{message} = $message;
    return $options;
}

1;

package Jsonl;

use strict;
use warnings;

our $VERSION = '0.01';

use JSON::PP ();

# One decoder for the whole package: canonical ordering keeps output stable
# between runs, and utf8 lets the CLI hand back real UTF-8 bytes.
my $ENCODER = JSON::PP->new->canonical->utf8;
my $DECODER = JSON::PP->new->utf8;

sub encoder { return $ENCODER }
sub decoder { return $DECODER }

# JSON null decodes to undef, which is indistinguishable from "key missing".
# JSON::PP::Boolean objects are the only scalars that need care, so helpers
# that walk documents test with exists() rather than defined().

sub encode {
    my ($value) = @_;
    return $ENCODER->encode($value);
}

sub decode_line {
    my ($line, $number) = @_;

    $number = 0 unless defined $number;

    my $value = eval { $DECODER->decode($line) };
    if (my $error = $@) {
        chomp $error;
        die sprintf("line %d: not valid JSON (%s)\n", $number, $error);
    }

    return $value;
}

# Splits a path like "a.b[0].c" into ('a', 'b', 0, 'c').
# Returns a list; a malformed path dies with a message the CLI shows as-is.
sub split_path {
    my ($path) = @_;

    die "empty path\n" unless defined $path && length $path;

    my @parts;
    my $rest = $path;
    while (length $rest) {
        if ($rest =~ s/\A\.?([^.\[\]]+)//) {
            push @parts, $1;
        }
        elsif ($rest =~ s/\A\[(\d+)\]//) {
            push @parts, 0 + $1;
        }
        else {
            die "malformed path '$path'\n";
        }
    }

    return @parts;
}

# Returns (found, value). A JSON null is found but undef.
sub fetch {
    my ($document, $path) = @_;

    my @parts = ref $path eq 'ARRAY' ? @{$path} : split_path($path);
    my $node = $document;

    for my $part (@parts) {
        if (ref $node eq 'HASH') {
            return (0, undef) unless exists $node->{$part};
            $node = $node->{$part};
        }
        elsif (ref $node eq 'ARRAY') {
            return (0, undef) unless $part =~ /\A\d+\z/;
            return (0, undef) if $part > $#$node;
            $node = $node->[$part];
        }
        else {
            return (0, undef);
        }
    }

    return (1, $node);
}

sub value_at {
    my ($document, $path) = @_;
    my (undef, $value) = fetch($document, $path);
    return $value;
}

# Rebuilds a nested document from a list of dotted paths, so
# --fields user.name,id produces {"id":…,"user":{"name":…}}.
sub pick {
    my ($document, @paths) = @_;

    my %result;
    for my $path (@paths) {
        my @parts = split_path($path);
        my ($found, $value) = fetch($document, \@parts);
        next unless $found;

        my @walk = @parts;
        my $leaf = pop @walk;
        my $cursor = \%result;
        for my $part (@walk) {
            $cursor->{$part} = {}
              unless ref $cursor->{$part} eq 'HASH';
            $cursor = $cursor->{$part};
        }
        $cursor->{$leaf} = $value;
    }

    return \%result;
}

# Everything that is not a container renders as text; booleans follow JSON
# spelling so filters and sort keys agree with what the file says.
sub text_of {
    my ($value) = @_;

    return '' unless defined $value;
    return 'true' if JSON::PP::is_bool($value) && $value;
    return 'false' if JSON::PP::is_bool($value);
    return $ENCODER->encode($value) if ref $value;
    return "$value";
}

# True when the scalar is a number the way a data file means it (no leading
# plus, no trailing junk, and JSON::PP already handed us a plain scalar).
sub looks_numeric {
    my ($value) = @_;

    return 0 unless defined $value && !ref $value;
    return 0 if JSON::PP::is_bool($value);
    return $value =~ /\A-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][-+]?[0-9]+)?\z/ ? 1 : 0;
}

1;

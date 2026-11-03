package Textstat::Counts;

use strict;
use warnings;

# Pure data and pure arithmetic: nothing here reads a file or prints, so the
# tests can drive every branch without touching the filesystem.

sub new {
    my ($class, %args) = @_;

    return bless {
        lines => defined $args{lines} ? $args{lines} : 0,
        words => defined $args{words} ? $args{words} : 0,
        bytes => defined $args{bytes} ? $args{bytes} : 0,
    }, $class;
}

# Count newline terminators, runs of non-whitespace, and raw bytes. Bytes, not
# characters, is what `wc -c` reports and it stays correct for input that is
# not valid UTF-8, which is why callers read files in raw mode.
sub of {
    my ($class, $text) = @_;
    $text = '' unless defined $text;

    my $lines = () = $text =~ /\n/g;
    my @words = $text =~ /\S+/g;

    return $class->new(
        lines => $lines,
        words => scalar @words,
        bytes => length $text,
    );
}

sub lines { return $_[0]->{lines} }
sub words { return $_[0]->{words} }
sub bytes { return $_[0]->{bytes} }

sub plus {
    my ($self, $other) = @_;

    return ref($self)->new(
        lines => $self->lines + $other->lines,
        words => $self->words + $other->words,
        bytes => $self->bytes + $other->bytes,
    );
}

1;

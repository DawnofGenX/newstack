package Textstat;

use strict;
use warnings;

use Textstat::Counts;

our $VERSION = '0.01';

sub version { return $VERSION }

sub count_text {
    my ($text) = @_;

    return Textstat::Counts->of($text);
}

1;

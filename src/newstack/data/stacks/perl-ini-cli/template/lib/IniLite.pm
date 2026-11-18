package IniLite;

use strict;
use warnings;

use IniLite::Parse;

our $VERSION = '0.01';

sub version { return $VERSION }

# Facade only: parsing lives in IniLite::Parse so the tests can drive it
# without a file or a terminal.
sub parse_text {
    my ($class, $text) = @_;

    return IniLite::Parse->parse($text);
}

1;

package Jsonl::Stats;

use strict;
use warnings;

use Jsonl ();

our $VERSION = '0.01';

# Sums and counts stay exact for integers, so the mean is the only value that
# is allowed to be fractional.
sub numeric_stats {
    my ($rows, $path) = @_;

    my ($count, $sum, $min, $max) = (0, 0, undef, undef);
    for my $row (@{$rows}) {
        my ($found, $value) = Jsonl::fetch($row, $path);
        next unless $found && Jsonl::looks_numeric($value);
        $count++;
        $sum += $value;
        $min = $value if !defined $min || $value < $min;
        $max = $value if !defined $max || $value > $max;
    }

    die "no numeric values at '$path'\n" if $count == 0;

    my $mean = $sum / $count;
    return {
        count => $count,
        sum   => tidy($sum),
        mean  => tidy($mean),
        min   => tidy($min),
        max   => tidy($max),
    };
}

# 6.0 renders as 6, 6.5 stays 6.5: JSONL files should not grow a pointless
# ".0" just because Perl numbers are doubles.
sub tidy {
    my ($value) = @_;

    return $value unless defined $value;
    my $text = sprintf('%.10g', $value);
    return 0 + $text;
}

1;

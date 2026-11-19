package Jsonl::Query;

use strict;
use warnings;

use JSON::PP ();
use Jsonl ();

our $VERSION = '0.01';

my %NUMERIC = map { $_ => 1 } qw(gt ge lt le);

# Numbers compare numerically and everything else as text, which is what makes
# --gt 9 skip 10 only when the column really is numeric.
sub compare {
    my ($left, $right, $numeric) = @_;

    # --numeric means "coerce": text that is not a number counts as 0, which is
    # how a column of mixed values still gets a stable numeric order.
    if ($numeric) {
        no warnings 'numeric';
        return (0 + $left) <=> (0 + $right);
    }

    return $left <=> $right
      if Jsonl::looks_numeric($left) && Jsonl::looks_numeric($right);
    return Jsonl::text_of($left) cmp Jsonl::text_of($right);
}

# A where clause is {path, op, value, number, regex}.
sub parse_where {
    my (%args) = @_;

    my $path = $args{path};
    die "empty path\n" unless defined $path && length $path;

    my @ops = grep { defined $args{$_} } qw(eq ne gt ge lt le match);
    die "--where takes exactly one of --eq, --ne, --gt, --ge, --lt, --le, --match\n"
      if @ops > 1;

    my $op = @ops ? $ops[0] : 'truthy';
    my $value = @ops ? $args{$op} : undef;
    my $clause = { path => $path, op => $op, value => $value };

    if ($op eq 'match') {
        my $pattern = eval { qr/$value/ };
        die "invalid regular expression '$value'\n" if $@;
        $clause->{regex} = $pattern;
    }
    if ($NUMERIC{$op}) {
        die "--$op needs a number, got '$value'\n" unless Jsonl::looks_numeric($value);
        $clause->{number} = 0 + $value;
    }

    return $clause;
}

sub matches {
    my ($row, $clause) = @_;

    my ($found, $value) = Jsonl::fetch($row, $clause->{path});
    my $op = $clause->{op};

    if ($op eq 'truthy') {
        return 0 unless $found && defined $value;
        return 0 if JSON::PP::is_bool($value) && !$value;
        return 0 if Jsonl::looks_numeric($value) && $value == 0;
        return length(Jsonl::text_of($value)) ? 1 : 0;
    }

    if ($op eq 'eq') {
        return 0 unless $found;
        return compare($value, $clause->{value}, 0) == 0 ? 1 : 0;
    }

    if ($op eq 'ne') {
        return 1 unless $found;
        return compare($value, $clause->{value}, 0) == 0 ? 0 : 1;
    }

    if ($op eq 'match') {
        return 0 unless $found && defined $value;
        return Jsonl::text_of($value) =~ $clause->{regex} ? 1 : 0;
    }

    # Numeric comparisons only ever match present numbers.
    return 0 unless $found && Jsonl::looks_numeric($value);
    my $difference = $value <=> $clause->{number};
    return 1 if $op eq 'gt' && $difference > 0;
    return 1 if $op eq 'ge' && $difference >= 0;
    return 1 if $op eq 'lt' && $difference < 0;
    return 1 if $op eq 'le' && $difference <= 0;
    return 0;
}

1;

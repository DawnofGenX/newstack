package CsvQuery::Parser;

use strict;
use warnings;

# RFC 4180-ish CSV parser. Returns arrayref of rows (arrayref of fields).
sub parse_csv {
    my ($text) = @_;
    $text = '' unless defined $text;
    my @rows;
    my $row = [];
    my $field = '';
    my $in_quotes = 0;
    my $at_start = 1;
    my @chars = split //, $text;
    my $i = 0;
    while ($i < scalar @chars) {
        my $c = $chars[$i];
        if ($in_quotes) {
            if ($c eq '"') {
                if ($i + 1 < scalar @chars && $chars[$i+1] eq '"') {
                    $field .= '"';
                    $i += 2;
                    next;
                } else {
                    $in_quotes = 0;
                    $i++;
                    next;
                }
            } else {
                $field .= $c;
                $i++;
                next;
            }
        } else {
            if ($at_start && $c eq '"') {
                $in_quotes = 1;
                $at_start = 0;
                $i++;
                next;
            }
            if ($c eq ',') {
                push @$row, $field;
                $field = '';
                $at_start = 1;
                $i++;
                next;
            }
            if ($c eq "\n") {
                push @$row, $field;
                push @rows, $row;
                $row = [];
                $field = '';
                $at_start = 1;
                $i++;
                next;
            }
            if ($c eq "\r") {
                $i++;
                next;
            }
            $field .= $c;
            $at_start = 0;
            $i++;
            next;
        }
    }
    # trailing field/row
    if ($field ne '' || @$row || $at_start == 0) {
        push @$row, $field;
        push @rows, $row;
    }
    # remove completely empty trailing row from final newline? keep parity with wc? We'll keep non-empty
    return \@rows;
}

1;
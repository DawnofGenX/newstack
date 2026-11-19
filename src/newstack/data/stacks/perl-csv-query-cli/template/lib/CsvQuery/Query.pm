package CsvQuery::Query;

use strict;
use warnings;

sub headers {
    my ($rows) = @_;
    return [] unless @$rows;
    return $rows->[0];
}

sub col_index {
    my ($headers, $name) = @_;
    for my $i (0 .. $#$headers) {
        return $i if $headers->[$i] eq $name;
    }
    return -1;
}

sub select_columns {
    my ($rows, @names) = @_;
    return $rows unless @names;
    my $hdr = $rows->[0];
    my @idx;
    for my $n (@names) {
        my $i = col_index($hdr, $n);
        push @idx, $i;
    }
    my @out;
    for my $r (@$rows) {
        my @row;
        for my $i (@idx) {
            push @row, ($i >= 0 ? $r->[$i] : '');
        }
        push @out, \@row;
    }
    return \@out;
}

sub filter_rows {
    my ($rows, $col, $val) = @_;
    return $rows unless defined $col;
    my $hdr = $rows->[0];
    my $i = col_index($hdr, $col);
    return $rows if $i < 0;
    my @out = ($rows->[0]);
    for my $r (@$rows[1..$#$rows]) {
        push @out, $r if defined $r->[$i] && $r->[$i] eq $val;
    }
    return \@out;
}

sub sum_column {
    my ($rows, $col) = @_;
    my $hdr = $rows->[0];
    my $i = col_index($hdr, $col);
    return 0 if $i < 0;
    my $sum = 0;
    for my $r (@$rows[1..$#$rows]) {
        my $v = $r->[$i];
        $sum += $v if defined $v && $v =~ /^-?\d+(\.\d+)?$/;
    }
    return $sum;
}

sub to_csv {
    my ($rows) = @_;
    my @lines;
    for my $r (@$rows) {
        my @fields = map { (defined $_ && ($_ =~ /[",\n]/)) ? '"' . ($_ =~ s/"/""/gr) . '"' : (defined $_ ? $_ : '') } @$r;
        push @lines, join(',', @fields);
    }
    return join("\n", @lines) . "\n";
}

1;
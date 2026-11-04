# Counting bytes. A Buf goes in, a Counts object comes out: no file, no terminal.
unit module Textstat::Counts;

class Counts is export {
    has UInt $.lines = 0;
    has UInt $.words = 0;
    has UInt $.bytes = 0;
}

# space, tab, newline, carriage return, vertical tab, form feed
sub is-space-byte(UInt $byte --> Bool) is export {
    $byte == 32 || $byte == 9 || $byte == 10 || $byte == 13 || $byte == 11 || $byte == 12;
}

sub counts-of(Buf:D $data --> Counts) is export {
    my UInt $lines = 0;
    my UInt $words = 0;
    my Bool $in-word = False;

    for $data.list -> UInt $byte {
        if $byte == 10 {
            $lines += 1;
            $in-word = False;
        }
        elsif is-space-byte($byte) {
            $in-word = False;
        }
        elsif not $in-word {
            $words += 1;
            $in-word = True;
        }
    }

    return Counts.new(:$lines, :$words, bytes => $data.elems);
}

sub counts-add(Counts $left, Counts $right --> Counts) is export {
    return Counts.new(lines => $left.lines + $right.lines,
                      words => $left.words + $right.words,
                      bytes => $left.bytes + $right.bytes);
}

# The figures in the order wc prints them, whichever flags asked for them.
sub counts-columns(@figures, Counts $tally --> List) is export {
    return @figures.map(-> Str $figure {
        given $figure {
            when 'lines' { $tally.lines }
            when 'words' { $tally.words }
            default      { $tally.bytes }
        }
    }).List;
}

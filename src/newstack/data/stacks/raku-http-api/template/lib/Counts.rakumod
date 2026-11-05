unit module Counts;

# wc's notion of a separator: exactly these six, nothing else. \s would also
# swallow Unicode spaces such as NO-BREAK SPACE, which wc does not.
my constant SPACE = set(' ', "\x09", "\x0a", "\x0d", "\x0b", "\x0c");

#| Count lines, words and bytes the way wc does.
sub count-text(Str $text --> Hash) is export {
    my int $lines = 0;
    my int $words = 0;
    my Bool $in-word = False;
    for $text.comb -> $char {
        $lines++ if $char eq "\x0a";
        if SPACE{$char} {
            $in-word = False;
        }
        elsif !$in-word {
            $words++;
            $in-word = True;
        }
    }
    return %(
        lines => $lines,
        words => $words,
        bytes => $text.encode('utf-8').bytes,
    );
}

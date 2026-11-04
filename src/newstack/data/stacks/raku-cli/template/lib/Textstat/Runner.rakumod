# Everything the CLI decides, with the four side effects handed in: reading a
# file, reading standard input, writing a line out, writing a line to stderr.
unit module Textstat::Runner;

use Textstat::Counts;
use Textstat::Options;

# wc's padding, copied rather than guessed: one figure from one readable
# operand is not padded at all; anything read from a pipe gets the widest cell
# wc ever needs; otherwise the width is the digit count of the total byte count.
sub row-width(List $figures, @rows, Bool $pipe, UInt $total-bytes --> UInt) {
    if $figures.elems == 1 and @rows.elems <= 1 {
        return 1 if @rows.elems == 0;
        my $value = counts-columns($figures, @rows[0]<value>).head;
        return max(1, $value.Str.chars);
    }
    return 7 if $pipe;
    return max(1, $total-bytes.Str.chars);
}

sub row-text(List $figures, Counts $tally, UInt $width --> Str) {
    return counts-columns($figures, $tally).map(-> UInt $value { $value.fmt("%{$width}d") }).join(' ');
}

# A reader either answers with bytes or with Nil. An empty file is still an
# answer, so the check is defined-ness rather than truth.
sub attempt(&reader) {
    my $data;
    my $ok = (try { $data = reader(); True }) // False;
    # A soft failure is still a failure: it only throws when someone uses it.
    $ok = False if $data ~~ Failure;
    return $ok ?? $data !! Nil;
}

sub run(@args, &read-file, &read-stdin, &write-out, &write-err --> Int) is export {
    my $parsed = parse-args(@args);

    given $parsed.status {
        when 'help' {
            write-out(usage(program-name()));
            return 0;
        }
        when 'version' {
            write-out(VERSION ~ "\n");
            return 0;
        }
        when 'usage-error' {
            write-err(program-name() ~ ": " ~ $parsed.message ~ "\n");
            write-err("Try '" ~ program-name() ~ " --help' for more information.\n");
            return 2;
        }
    }

    my List $figures = $parsed.figures;
    my @operands = $parsed.files;
    my Bool $implicit = @operands.elems == 0;
    @operands = ('-',) if $implicit;
    my Bool $pipe = @operands.grep(* eq '-').elems > 0;

    my @rows;
    my Counts $total = Counts.new;
    my Bool $failed = False;

    for @operands -> Str $path {
        my $data = attempt(-> { $path eq '-' ?? read-stdin() !! read-file($path) });

        if not $data.defined {
            write-err("error: cannot open '" ~ $path ~ "'\n");
            $failed = True;
            next;
        }

        my Counts $tally = counts-of($data);
        @rows.push({label => ($implicit ?? '' !! $path), value => $tally});
        $total = counts-add($total, $tally);
    }

    my UInt $width = row-width($figures, @rows, $pipe, $total.bytes);

    for @rows -> $row {
        my Str $line = row-text($figures, $row<value>, $width);
        write-out($implicit ?? $line ~ "\n" !! $line ~ ' ' ~ $row<label> ~ "\n");
    }

    if @operands.elems > 1 {
        write-out(row-text($figures, $total, $width) ~ " total\n");
    }

    return $failed ?? 1 !! 0;
}

sub program-name(--> Str) is export { "{{ npm_name }}" }

# argv in, a decision out. This module never opens a file and never prints.
unit module Textstat::Options;

class Parsed is export {
    has Str $.status = 'ok';
    has Str $.message = '';
    has @.figures;
    has @.files;
}

constant VERSION is export = '0.1.0';

sub usage(Str $program --> Str) is export {
    return "Usage: $program \[OPTION]... \[FILE]...\n"
         ~ "Print newline, word, and byte counts for each FILE.\n"
         ~ "\n"
         ~ "  -l, --lines    print the newline count\n"
         ~ "  -w, --words    print the word count\n"
         ~ "  -c, --bytes    print the byte count\n"
         ~ "  -h, --help     show this help and exit\n"
         ~ "  -V, --version  show the version and exit\n"
         ~ "\n"
         ~ "With no FILE, or when FILE is -, read standard input.\n";
}

# wc prints the figures in this order however they were asked for.
sub canonical(@figures --> List) {
    return ('lines', 'words', 'bytes').grep(-> $figure { $figure eq any(@figures) }).List;
}

sub parse-args(@args) is export {
    my $status = 'ok';
    my $message = '';
    my @figures;
    my @files;
    my $only = False;

    for @args -> Str $word {
        if $status ne 'ok' {
            next;
        }
        if not $only and $word eq '--' {
            $only = True;
            next;
        }
        if not $only and $word eq '-' {
            @files.push($word);
            next;
        }
        if not $only and $word.chars > 1 and $word.substr(0, 2) eq '--' {
            my $name = $word.substr(2);
            given $name {
                when 'lines'   { @figures.push('lines') unless 'lines' (elem) @figures }
                when 'words'   { @figures.push('words') unless 'words' (elem) @figures }
                when 'bytes'   { @figures.push('bytes') unless 'bytes' (elem) @figures }
                when 'help'    { $status = 'help' }
                when 'version' { $status = 'version' }
                default        { $status = 'usage-error'; $message = "unknown option: $word" }
            }
            next;
        }
        if not $only and $word.chars > 1 and $word.substr(0, 1) eq '-' {
            for $word.substr(1).comb -> Str $letter {
                given $letter {
                    when 'l' { @figures.push('lines') unless 'lines' (elem) @figures }
                    when 'w' { @figures.push('words') unless 'words' (elem) @figures }
                    when 'c' { @figures.push('bytes') unless 'bytes' (elem) @figures }
                    when 'h' { $status = 'help'; last }
                    when 'V' { $status = 'version'; last }
                    default  { $status = 'usage-error'; $message = "unknown option: -$letter"; last }
                }
            }
            next;
        }
        @files.push($word);
    }

    my @shown = ($status eq 'ok' and @figures) ?? canonical(@figures) !! ('lines', 'words', 'bytes');
    return Parsed.new(:$status, :$message, figures => @shown, files => @files);
}

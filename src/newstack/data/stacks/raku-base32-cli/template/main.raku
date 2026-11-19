
use Base32;

sub usage() {
    return "Usage: base32-cli encode [TEXT]\n       base32-cli decode [TEXT]\n";
}

my @args = @*ARGS;
if @args.elems == 0 {
    print usage();
    exit 2;
}
if @args[0] eq '--help' || @args[0] eq '-h' {
    print usage();
    exit 0;
}
if @args.elems < 2 {
    print usage();
    exit 2;
}
my ($cmd, $val) = @args;
try {
    if $cmd eq 'encode' {
        my $data = defined($val) ?? $val.encode('utf-8').Buf !! $*IN.slurp(:bin);
        say base32-encode($data);
    } elsif $cmd eq 'decode' {
        my $text = defined($val) ?? $val !! $*IN.slurp;
        say base32-decode-text($text);
    } else {
        print usage();
        exit 2;
    }
    exit 0;
    CATCH {
        default {
            note $!;
            exit 1;
        }
    }
}

# The only file that touches the real process: three handles and an exit code.
use Textstat::Counts;
use Textstat::Options;
use Textstat::Runner;

sub read-bytes(Str $path --> Buf) {
    my $handle = $path.IO.open(:bin) orelse die "cannot open $path";
    my $data = $handle.read;
    $handle.close;
    return $data // Buf.new;
}

sub read-standard-input(--> Buf) {
    return $*IN.slurp(:bin) // Buf.new;
}

sub write-line(Str $text) {
    $*OUT.print($text);
    $*OUT.flush;
}

sub write-error-line(Str $text) {
    $*ERR.print($text);
    $*ERR.flush;
}

exit run(@*ARGS, &read-bytes, &read-standard-input, &write-line, &write-error-line);

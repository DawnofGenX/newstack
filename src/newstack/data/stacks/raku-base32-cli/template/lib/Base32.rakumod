
unit module Base32;

my constant @ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567'.comb;

sub base32-encode(Buf:D $data --> Str) is export {
    return '' if $data.elems == 0;
    my $out = '';
    my int $i = 0;
    my @keep = (2, 4, 5, 7, 8);
    while $i < $data.elems {
        my @chunk;
        my int $orig = 0;
        for 0..4 -> $j {
            my int $idx = $i + $j;
            if $idx < $data.elems {
                @chunk.push($data[$idx]);
                $orig++;
            } else {
                @chunk.push(0);
            }
        }
        my int $val = 0;
        for @chunk -> $b { $val = ($val +< 8) + $b; }
        my @chars;
        for 1..8 -> $k {
            my int $shift = 40 - ($k * 5);
            my int $idxv = ($val +> $shift) +& 0x1F;
            @chars.push(@ALPHABET[$idxv]);
        }
        my int $k = @keep[$orig - 1];
        $out ~= @chars[0 .. $k - 1].join;
        if $k < 8 { $out ~= '=' x (8 - $k); }
        $i += 5;
    }
    return $out;
}

sub base32-encode-text(Str:D $text --> Str) is export {
    return base32-encode($text.encode('utf-8').Buf);
}

sub base32-decode(Str:D $text --> Buf) is export {
    my $s = $text.uc.subst(/\s/, '', :g);
    my $clean = $s.subst('=', '', :g);
    my %map;
    for @ALPHABET.kv -> $idx, $c { %map{$c} = $idx; }
    my @vals;
    for $clean.comb -> $c {
        die "invalid base32 character: $c" unless %map{$c}:exists;
        @vals.push(%map{$c});
    }
    return Buf.new if @vals.elems == 0;
    my Buf $buf = Buf.new;
    my int $i = 0;
    my %nmap = 2 => 1, 4 => 2, 5 => 3, 7 => 4, 8 => 5;
    while $i < @vals.elems {
        my @chunk;
        for 0..7 -> $j {
            my int $idx = $i + $j;
            if $idx < @vals.elems {
                @chunk.push(@vals[$idx]);
            } else {
                @chunk.push(0);
            }
        }
        my int $val = 0;
        for @chunk -> $v { $val = ($val +< 5) + $v; }
        my @bytes = (
            ($val +> 32) +& 0xFF,
            ($val +> 24) +& 0xFF,
            ($val +> 16) +& 0xFF,
            ($val +> 8) +& 0xFF,
            $val +& 0xFF,
        );
        my int $nchars = min(8, @vals.elems - $i);
        my int $nb = %nmap{$nchars} // 0;
        for 0 .. $nb - 1 -> $j { $buf.push(@bytes[$j]); }
        $i += 8;
    }
    return $buf;
}

sub base32-decode-text(Str:D $text --> Str) is export {
    return base32-decode($text).decode('utf-8');
}

unit module Json;

# Rakudo's core ships no JSON parser, and the two libraries people reach for
# (JSON::Fast, JSON::Tiny) are installs this stack refuses to need. What a
# service needs is small: validate a whole document, and keep a string apart
# from a number. That is what this module does.

#| Parse a request body. Returns {kind => 'text', text => …}, {kind => 'missing'}
#| when the document is an object without a string "text", or {kind => 'invalid'}
#| when it is not a JSON object at all.
sub read-body(Str $raw --> Hash) is export {
    my %state = (text => $raw, pos => 0);
    my $value;
    my Bool $ok = True;
    try {
        $value = parse-value(%state);
        skip-space(%state);
        die 'trailing data' if %state<pos> < %state<text>.chars;
        CATCH {
            default { $ok = False }
        }
    }
    return %(kind => 'invalid') unless $ok;
    return %(kind => 'invalid') unless $value ~~ Hash;
    my $text = $value<text>;
    return %(kind => 'missing') unless $text ~~ Str;
    return %(kind => 'text', text => $text);
}

my sub die-bad(Str $why) { die $why }

my sub skip-space(%state) {
    my Str $text = %state<text>;
    my int $pos = %state<pos>;
    $pos++ while $pos < $text.chars && $text.substr($pos, 1) ~~ /^<[\x20\t\n\r]>$/;
    %state<pos> = $pos;
}

my sub expect(%state, Str $word) {
    my Str $text = %state<text>;
    my int $pos = %state<pos>;
    die-bad("expected $word") unless $text.substr($pos, $word.chars) eq $word;
    %state<pos> = $pos + $word.chars;
}

my sub parse-value(%state) {
    skip-space(%state);
    my Str $text = %state<text>;
    my int $pos = %state<pos>;
    die-bad('unexpected end') if $pos >= $text.chars;
    my Str $char = $text.substr($pos, 1);
    return parse-string(%state) if $char eq '"';
    return parse-object(%state) if $char eq '{';
    return parse-array(%state) if $char eq '[';
    return do { expect(%state, 'true'); True } if $char eq 't';
    return do { expect(%state, 'false'); False } if $char eq 'f';
    return do { expect(%state, 'null'); Any } if $char eq 'n';
    return parse-number(%state);
}

my sub parse-number(%state) {
    my Str $rest = %state<text>.substr(%state<pos>);
    my $match = $rest.match(/^ '-'? \d+ [ '.' \d+ ]? [ <[eE]> <[+-]>? \d+ ]? /);
    die-bad('not a number') without $match;
    %state<pos> = %state<pos> + $match.Str.chars;
    return +$match.Str;
}

my sub parse-string(%state) {
    my Str $text = %state<text>;
    my int $pos = %state<pos>;
    die-bad('expected a string') unless $text.substr($pos, 1) eq '"';
    $pos++;
    my Str $out = '';
    loop {
        die-bad('unterminated string') if $pos >= $text.chars;
        my Str $char = $text.substr($pos, 1);
        if $char eq '"' {
            %state<pos> = $pos + 1;
            return $out;
        }
        if $char eq '\\' {
            die-bad('unterminated escape') if $pos + 1 >= $text.chars;
            my Str $escape = $text.substr($pos + 1, 1);
            $pos += 2;
            given $escape {
                when '"' { $out ~= '"' }
                when '\\' { $out ~= '\\' }
                when '/' { $out ~= '/' }
                when 'b' { $out ~= "\x08" }
                when 'f' { $out ~= "\x0c" }
                when 'n' { $out ~= "\x0a" }
                when 'r' { $out ~= "\x0d" }
                when 't' { $out ~= "\x09" }
                when 'u' {
                    my int $code = hex4($text, $pos);
                    $pos += 4;
                    # A surrogate pair is two escapes; a lone one is a code point
                    # that cannot be encoded, so it stays a replacement char.
                    if $code >= 0xD800 && $code <= 0xDBFF && $text.substr($pos, 2) eq '\\u' {
                        my int $low = hex4($text, $pos + 2);
                        if $low >= 0xDC00 && $low <= 0xDFFF {
                            $code = 0x10000 + (($code - 0xD800) * 0x400) + ($low - 0xDC00);
                            $pos += 6;
                        }
                    }
                    $out ~= chr($code);
                }
                default { die-bad("unknown escape \\$escape") }
            }
            next;
        }
        $out ~= $char;
        $pos++;
    }
}

my sub hex4(Str $text, int $at --> Int) {
    my Str $digits = $text.substr($at, 4);
    die-bad('bad \\u escape') unless $digits ~~ /^<[0..9A..Fa..f]> ** 4$/;
    return :16($digits);
}

my sub parse-object(%state) {
    %state<pos> = %state<pos> + 1;
    my %hash;
    skip-space(%state);
    if %state<text>.substr(%state<pos>, 1) eq '}' {
        %state<pos> = %state<pos> + 1;
        return %hash;
    }
    loop {
        skip-space(%state);
        my Str $key = parse-string(%state);
        skip-space(%state);
        die-bad('expected a colon') unless %state<text>.substr(%state<pos>, 1) eq ':';
        %state<pos> = %state<pos> + 1;
        %hash{$key} = parse-value(%state);
        skip-space(%state);
        my Str $char = %state<text>.substr(%state<pos>, 1);
        %state<pos> = %state<pos> + 1;
        last if $char eq '}';
        die-bad('expected a comma or a closing brace') unless $char eq ',';
    }
    return %hash;
}

my sub parse-array(%state) {
    %state<pos> = %state<pos> + 1;
    my @items;
    skip-space(%state);
    if %state<text>.substr(%state<pos>, 1) eq ']' {
        %state<pos> = %state<pos> + 1;
        return @items;
    }
    loop {
        @items.push(parse-value(%state));
        skip-space(%state);
        my Str $char = %state<text>.substr(%state<pos>, 1);
        %state<pos> = %state<pos> + 1;
        last if $char eq ']';
        die-bad('expected a comma or a closing bracket') unless $char eq ',';
    }
    return @items;
}

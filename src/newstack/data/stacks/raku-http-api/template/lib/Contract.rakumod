use Counts;
use Json;

unit module Contract;

#| One reply: an HTTP status and a JSON body, already serialised.
sub reply(Int $status, Str $body --> Hash) is export {
    return %(status => $status, body => $body);
}

#| Quote a string for JSON. The order of the keys in a reply is ours to choose,
#| so the body is built by hand rather than through a hash.
sub json-quote(Str $value --> Str) is export {
    my Str $out = '"';
    for $value.comb -> $char {
        my int $code = $char.ord;
        if $char eq '"' {
            $out ~= '\\"';
        }
        elsif $char eq '\\' {
            $out ~= '\\\\';
        }
        elsif $char eq "\x0a" {
            $out ~= '\\n';
        }
        elsif $char eq "\x0d" {
            $out ~= '\\r';
        }
        elsif $char eq "\x09" {
            $out ~= '\\t';
        }
        elsif $char eq "\x08" {
            $out ~= '\\b';
        }
        elsif $char eq "\x0c" {
            $out ~= '\\f';
        }
        elsif $code < 0x20 {
            $out ~= sprintf('\\u%04x', $code);
        }
        else {
            $out ~= $char;
        }
    }
    return $out ~ '"';
}

#| Percent-decode a query value the way a form decoder does: '+' is a space, and
#| the escapes are bytes, so %C3%A9 is one character and not two.
sub percent-decode(Str $raw --> Str) is export {
    my $bytes = Buf.new;
    my @chars = $raw.comb;
    my int $index = 0;
    while $index < @chars.elems {
        my Str $char = @chars[$index];
        if $char eq '%' && $index + 2 < @chars.elems {
            my Str $hex = @chars[$index + 1] ~ @chars[$index + 2];
            if $hex ~~ /^<[0..9A..Fa..f]> ** 2$/ {
                $bytes.push(:16($hex));
                $index += 3;
                next;
            }
        }
        $bytes.push(|($char eq '+' ?? ' ' !! $char).encode('utf-8'));
        $index++;
    }
    return $bytes.decode('utf-8');
}

my sub query-params(Str $query --> Hash) {
    my %params;
    my Str $raw = $query.chars && $query.starts-with('?') ?? $query.substr(1) !! $query;
    return %params unless $raw.chars;
    for $raw.split('&') -> $pair {
        next unless $pair.chars;
        my @halves = $pair.split('=', 2);
        my Str $name = percent-decode(@halves[0]);
        next if %params{$name}:exists;
        %params{$name} = @halves.elems > 1 ?? percent-decode(@halves[1]) !! '';
    }
    return %params;
}

my sub stats-body(Str $text --> Str) {
    my %counts = count-text($text);
    return '{"text":' ~ json-quote($text)
        ~ ',"lines":' ~ %counts<lines>
        ~ ',"words":' ~ %counts<words>
        ~ ',"bytes":' ~ %counts<bytes> ~ '}';
}

my sub error(Int $status, Str $code, Str $detail? --> Hash) {
    return reply($status, '{"error":' ~ json-quote($code) ~ '}') unless $detail.defined;
    return reply($status, '{"error":' ~ json-quote($code) ~ ',"detail":' ~ json-quote($detail) ~ '}');
}

#| The whole HTTP contract, with no socket in sight: method, path, query and
#| body in; status and JSON body out.
sub route(Str $method, Str $path, Str $query, Str $body --> Hash) is export {
    if $method eq 'GET' && $path eq '/health' {
        return reply(200, '{"status":"ok"}');
    }
    if $method eq 'GET' && $path eq '/stats' {
        my %params = query-params($query);
        return error(422, 'missing_text') unless %params{'text'}:exists;
        return reply(200, stats-body(%params{'text'}));
    }
    if $method eq 'POST' && $path eq '/stats' {
        my %read = read-body($body);
        return error(422, 'invalid_json') if %read<kind> eq 'invalid';
        return error(422, 'missing_text') if %read<kind> eq 'missing';
        return reply(200, stats-body(%read<text>));
    }
    if $path eq '/health' || $path eq '/stats' {
        return error(405, 'method_not_allowed');
    }
    return error(404, 'not_found', "no route for $method $path");
}

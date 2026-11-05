use Contract;

unit module Server;

my constant $MAX-HEAD = 16384;
my constant $MAX-BODY = 65536;

#| Bind and answer one connection at a time. Raku's sockets have no worker pool,
#| and a counting service does not need one.
sub serve(Str $host, Int $port) is export {
    my $listener = IO::Socket::INET.new(
        :listen,
        :localhost($host),
        :localport($port),
        :reuseaddr,
    );
    note "listening on http://$host:$port";
    loop {
        my $connection = $listener.accept or next;
        try {
            handle($connection);
            CATCH {
                default { note "request failed: $_" }
            }
        }
        $connection.close;
    }
}

my sub handle($connection) {
    my $head = Buf.new;
    while $head.elems < $MAX-HEAD {
        my $byte = $connection.read(1);
        last without $byte;
        last if $byte.elems == 0;
        $head.push(|$byte);
        last if $head.elems >= 4
            && $head[*-4] == 13 && $head[*-3] == 10
            && $head[*-2] == 13 && $head[*-1] == 10;
    }
    unless $head.elems >= 4 && $head[*-4] == 13 && $head[*-3] == 10
        && $head[*-2] == 13 && $head[*-1] == 10 {
        send-reply($connection, 400, '{"error":"invalid_json"}');
        return;
    }
    my Str $text = $head.decode('utf-8');
    my @lines = $text.split("\r\n");
    my Str $request-line = @lines.shift // '';
    my @parts = $request-line.split(' ').grep(*.chars);
    unless @parts.elems >= 2 {
        send-reply($connection, 400, '{"error":"invalid_json"}');
        return;
    }
    my Str $method = @parts[0];
    my Str $target = @parts[1];
    my int $length = 0;
    for @lines -> $line {
        my $colon = $line.index(':');
        next without $colon;
        my Str $name = $line.substr(0, $colon).trim.lc;
        $length = $line.substr($colon + 1).trim.Int if $name eq 'content-length';
    }
    if $length > $MAX-BODY {
        send-reply($connection, 413, '{"error":"body_too_large"}');
        return;
    }
    my $body = Buf.new;
    while $body.elems < $length {
        my $chunk = $connection.read($length - $body.elems);
        last if $chunk.elems == 0;
        $body.push(|$chunk);
    }
    my Str $payload = $body.elems ?? $body.decode('utf-8') !! '';
    my Str $path = $target;
    my Str $query = '';
    my $mark = $target.index('?');
    with $mark {
        $path = $target.substr(0, $mark);
        $query = $target.substr($mark + 1);
    }
    my %result = route($method, $path, $query, $payload);
    send-reply($connection, %result<status>, %result<body>);
}

my sub send-reply($connection, Int $status, Str $body) {
    my $payload = $body.encode('utf-8');
    my Str $head = "HTTP/1.1 $status {reason($status)}\r\n"
        ~ "content-type: application/json\r\n"
        ~ "content-length: {$payload.elems}\r\n"
        ~ "connection: close\r\n\r\n";
    $connection.write($head.encode('utf-8'));
    $connection.write($payload);
}

my sub reason(Int $status --> Str) {
    return 'OK' if $status == 200;
    return 'Bad Request' if $status == 400;
    return 'Not Found' if $status == 404;
    return 'Method Not Allowed' if $status == 405;
    return 'Payload Too Large' if $status == 413;
    return 'Unprocessable Entity' if $status == 422;
    return 'Internal Server Error';
}

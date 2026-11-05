package Textstat::Contract;

use strict;
use warnings;

use JSON::PP ();

use Textstat::Counts;

# The whole route table as a pure function: no Mojolicious, no sockets, so the
# test suite can pin every status code with a plain function call.
sub route {
    my ($class, $method, $path, $query, $body) = @_;

    $method = '' unless defined $method;
    $path   = '' unless defined $path;
    $query  = '' unless defined $query;
    $body   = '' unless defined $body;

    if ($method eq 'GET' && $path eq '/health') {
        return _reply(200, { status => 'ok' });
    }

    if ($method eq 'GET' && $path eq '/stats') {
        my $text = _query_param($query, 'text');
        return _error(422, 'missing_text') unless defined $text;
        return _stats($text);
    }

    if ($method eq 'POST' && $path eq '/stats') {
        my $payload = _decode_object($body);
        return _error(422, 'invalid_json') unless defined $payload;
        my $text = _string_member($payload, 'text');
        return _error(422, 'missing_text') unless defined $text;
        return _stats($text);
    }

    if ($path eq '/health' || $path eq '/stats') {
        return _error(405, 'method_not_allowed');
    }

    return _reply(404, { error => 'not_found', detail => "no route for $method $path" });
}

sub _stats {
    my ($text) = @_;
    my $counts = Textstat::Counts->of($text);
    return _reply(200, {
        text  => $text,
        lines => $counts->lines,
        words => $counts->words,
        bytes => $counts->bytes,
    });
}

sub _reply {
    my ($status, $payload) = @_;
    return {
        status => $status,
        body   => JSON::PP->new->utf8->canonical->encode($payload),
    };
}

sub _error {
    my ($status, $code) = @_;
    return _reply($status, { error => $code });
}

sub _decode_object {
    my ($body) = @_;
    my $data = eval { JSON::PP->new->utf8->decode($body) };
    return undef if $@;
    return undef unless ref $data eq 'HASH';
    return $data;
}

# JSON::PP decodes strings to PV and numbers to IV/NV, and re-encoding shows the
# difference: a string always comes back quoted, a number never does. That is
# how {"text": 42} is told apart from {"text": "42"}.
sub _string_member {
    my ($payload, $name) = @_;
    return undef unless exists $payload->{$name};
    my $value = $payload->{$name};
    return undef if ref $value;
    my $encoded = eval { JSON::PP->new->utf8->canonical->encode($value) };
    return undef if $@ || !defined $encoded || $encoded !~ /^"/;
    return $value;
}

sub _query_param {
    my ($query, $name) = @_;
    return undef unless length $query;
    for my $pair (split /&/, $query) {
        my ($key, $value) = split /=/, $pair, 2;
        next unless defined $key && $key eq $name;
        $value = '' unless defined $value;
        $value =~ tr/+/ /;
        $value =~ s/%([0-9A-Fa-f]{2})/chr hex $1/ge;
        return $value;
    }
    return undef;
}

1;

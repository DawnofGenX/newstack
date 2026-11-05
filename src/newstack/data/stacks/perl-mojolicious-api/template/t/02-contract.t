use strict;
use warnings;

use lib 'lib';

use Test::More;
use Textstat::Contract;

sub route { Textstat::Contract->route(@_) }

is_deeply(
    decode(route('GET', '/health', '', '')),
    { status => 200, body => { status => 'ok' } },
    'GET /health answers a JSON status object',
);

is_deeply(
    decode(route('GET', '/stats', 'text=hello%20world%0A', '')),
    { status => 200, body => { text => "hello world\n", lines => 1, words => 2, bytes => 12 } },
    'GET /stats counts the decoded query parameter',
);

is_deeply(
    decode(route('GET', '/stats', 'text=a+b%09c', '')),
    { status => 200, body => { text => "a b\tc", lines => 0, words => 3, bytes => 5 } },
    'a raw + is a space and %09 is a tab',
);

is(decode(route('GET', '/stats', '', ''))->{body}{error}, 'missing_text', 'GET without text is 422');
is(decode(route('GET', '/stats', 'other=1', ''))->{body}{error}, 'missing_text', 'an unrelated parameter is still missing text');

is_deeply(
    decode(route('POST', '/stats', '', '{"text": "a b\nc\n"}')),
    { status => 200, body => { text => "a b\nc\n", lines => 2, words => 3, bytes => 6 } },
    'POST /stats counts the posted text',
);

is_deeply(
    decode(route('POST', '/stats', '', '{"text": "  padded  \n"}'))->{body},
    { text => "  padded  \n", lines => 1, words => 1, bytes => 11 },
    'the text is echoed exactly as sent',
);

is(decode(route('POST', '/stats', '', '{"text": 42}'))->{body}{error}, 'missing_text', 'a numeric text is not a string');
is(decode(route('POST', '/stats', '', '{"text": "42"}'))->{status}, 200, 'a quoted number is a string');
is(decode(route('POST', '/stats', '', '{}'))->{body}{error}, 'missing_text', 'an object without text is 422');
is(decode(route('POST', '/stats', '', 'nope'))->{body}{error}, 'invalid_json', 'a broken body is 422 invalid_json');
is(decode(route('POST', '/stats', '', '[1,2]'))->{body}{error}, 'invalid_json', 'a JSON array is not an object');

is(decode(route('DELETE', '/health', '', ''))->{status}, 405, 'a known path with another method is 405');
is(decode(route('PUT', '/stats', '', ''))->{status}, 405, 'a known path with another method is 405');

is_deeply(
    decode(route('GET', '/nope', '', '')),
    { status => 404, body => { error => 'not_found', detail => 'no route for GET /nope' } },
    'an unknown route is a JSON 404',
);

is(decode(route('GET', '/stats', 'text=h%C3%A9llo%20w%C3%B6rld%0A', ''))->{body}{bytes},
    14, 'percent-encoded UTF-8 is counted in bytes');

sub decode {
    my ($reply) = @_;
    my $json = JSON::PP->new->utf8->decode($reply->{body});
    return { status => $reply->{status}, body => $json };
}

done_testing();

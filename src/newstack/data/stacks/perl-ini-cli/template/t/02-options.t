use strict;
use warnings;

use lib 'lib';

use Test::More;
use IniLite::Options;

my $defaults = IniLite::Options::parse();
is($defaults->{status}, 'ok', 'empty argv is ok');
is($defaults->{json}, 0, 'json is off by default');
is($defaults->{list}, 0, 'list-sections is off by default');
is_deeply($defaults->{files}, [], 'no files by default');

is(IniLite::Options::parse('--help')->{status}, 'help', '--help sets help');
is(IniLite::Options::parse('-h')->{status}, 'help', '-h sets help');
is(IniLite::Options::parse('-V')->{status}, 'version', '-V sets version');

is(IniLite::Options::parse('-s', 'db')->{section}, 'db', '-s takes the next argument');
is(IniLite::Options::parse('--section=db')->{section}, 'db', '--section=value works');
is(IniLite::Options::parse('-g', 'db.url')->{get}, 'db.url', '-g takes the next argument');
is(IniLite::Options::parse('--get=port')->{get}, 'port', '--get=value works');
is(IniLite::Options::parse('--json')->{json}, 1, '--json turns json on');
is(IniLite::Options::parse('--list-sections')->{list}, 1, '--list-sections turns list on');

my $missing = IniLite::Options::parse('--section');
is($missing->{status}, 'error', 'a missing option value is an error');
like($missing->{error}, qr/needs a value/, 'the error says a value is missing');

my $unknown = IniLite::Options::parse('--bogus');
is($unknown->{status}, 'error', 'an unknown flag is an error');
like($unknown->{error}, qr/unknown option '--bogus'/, 'the unknown flag is named');

my $after_dashes = IniLite::Options::parse('--', '--not-a-flag');
is_deeply($after_dashes->{files}, ['--not-a-flag'], '-- ends option parsing');
is_deeply(IniLite::Options::parse('-')->{files}, ['-'], 'a bare dash is a file');

like(IniLite::Options::usage('ini-lite'), qr/usage: ini-lite/, 'the usage line names the program');

done_testing();

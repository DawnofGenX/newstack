use strict;
use warnings;

use lib 'lib';

use Test::More;
use Textstat::Options;

my $default = Textstat::Options::parse();
is($default->{status}, 'ok', 'no arguments is a normal run');
is($default->{mode}, 'all', 'no flag selects every figure');
is_deeply($default->{files}, [], 'no arguments means read standard input');

is(Textstat::Options::parse('-l')->{mode}, 'lines', '-l selects lines');
is(Textstat::Options::parse('--words')->{mode}, 'words', '--words selects words');
is(Textstat::Options::parse('-c')->{mode}, 'bytes', '-c selects bytes');

my $files = Textstat::Options::parse('-c', 'a.txt', 'b.txt');
is($files->{status}, 'ok', 'flags and files mix');
is_deeply($files->{files}, ['a.txt', 'b.txt'], 'files keep their order');

is(Textstat::Options::parse('-h')->{status}, 'help', '-h asks for help');
is(Textstat::Options::parse('--help')->{status}, 'help', '--help asks for help');
is(Textstat::Options::parse('-V')->{status}, 'version', '-V asks for the version');
is(Textstat::Options::parse('--version')->{status}, 'version', '--version asks for the version');

my $conflict = Textstat::Options::parse('-l', '-w');
is($conflict->{status}, 'error', 'two modes is a usage error');
like($conflict->{error}, qr/conflicts/, 'the conflict is explained');

my $unknown = Textstat::Options::parse('--bogus');
is($unknown->{status}, 'error', 'an unknown flag is a usage error');
like($unknown->{error}, qr/unknown option '--bogus'/, 'the unknown flag is named');

is($unknown->{mode}, 'all', 'a usage error still reports a mode');

is_deeply(Textstat::Options::parse('--', '-l')->{files}, ['-l'], '-- stops option parsing');
is_deeply(Textstat::Options::parse('-')->{files}, ['-'], 'a lone dash is a file, not a flag');
is_deeply(Textstat::Options::parse('')->{files}, [''], 'an empty argument is a file');

like(Textstat::Options::usage('wordcount'), qr/usage: wordcount /, 'usage names the program');
like(Textstat::Options::usage('wordcount'), qr/-l, --lines/, 'usage documents every mode');
like(Textstat::Options::version, qr/\A\d+\.\d+\z/, 'version is a plain dotted number');

done_testing();

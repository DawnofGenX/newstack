use strict;
use warnings;

use lib 'lib';

use Test::More;
use Textstat;
use Textstat::Counts;

my $counts = Textstat::Counts->of("one two\nthree\n");
isa_ok($counts, 'Textstat::Counts', 'of() returns a Counts object');
is($counts->lines, 2, 'counts newline terminators');
is($counts->words, 3, 'counts whitespace separated words');
is($counts->bytes, 14, 'counts bytes, not characters');

my $empty = Textstat::Counts->of('');
is($empty->lines, 0, 'empty input has no lines');
is($empty->words, 0, 'empty input has no words');
is($empty->bytes, 0, 'empty input has no bytes');

my $unterminated = Textstat::Counts->of('one two');
is($unterminated->lines, 0, 'an unterminated last line is not counted, matching wc -l');
is($unterminated->words, 2, 'words without a trailing newline are counted');
is($unterminated->bytes, 7, 'bytes are the raw length');

my $padded = Textstat::Counts->of("  spaced   out  \n");
is($padded->words, 2, 'runs of whitespace do not create empty words');

my $wide = Textstat::Counts->of("na\xc3\xafve\n");
is($wide->bytes, 7, 'multi-byte characters count as their byte length');
is($wide->words, 1, 'a multi-byte word counts once');

my $made = Textstat::Counts->new(lines => 1, words => 2, bytes => 3);
is_deeply([$made->lines, $made->words, $made->bytes], [1, 2, 3], 'new() stores each figure');

my $sum = $counts->plus($made);
is($sum->lines, 3, 'plus() adds lines');
is($sum->words, 5, 'plus() adds words');
is($sum->bytes, 17, 'plus() adds bytes');
is($counts->lines, 2, 'plus() leaves the receiver unchanged');

is(Textstat::count_text("a b\n")->bytes, 4, 'the facade counts bytes through Counts');
is(Textstat->version, '0.01', 'the facade exposes the distribution version');

done_testing();

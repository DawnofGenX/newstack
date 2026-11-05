use strict;
use warnings;

use ExtUtils::MakeMaker;

WriteMakefile(
    NAME             => 'Textstat',
    VERSION          => '0.01',
    ABSTRACT         => 'A JSON service that counts lines, words and bytes',
    LICENSE          => 'mit',
    MIN_PERL_VERSION => '5.010',
    EXE_FILES        => ['bin/{{ npm_name }}'],
    PREREQ_PM        => {
        'JSON::PP'    => 0,
        'Mojolicious' => '9.30',
    },
    TEST_REQUIRES    => { 'Test::More' => 0 },
    test             => { TESTS => 't/*.t' },
);

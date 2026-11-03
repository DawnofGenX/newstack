use strict;
use warnings;

use ExtUtils::MakeMaker;

WriteMakefile(
    NAME             => 'Textstat',
    VERSION_FROM     => 'lib/Textstat.pm',
    ABSTRACT         => 'A small wc-style text counter',
    LICENSE          => 'mit',
    MIN_PERL_VERSION => '5.010',
    EXE_FILES        => ['bin/{{ npm_name }}'],
    PREREQ_PM        => { 'Test::More' => 0 },
    TEST_REQUIRES    => { 'Test::More' => 0 },
    test             => { TESTS => 't/*.t' },
);

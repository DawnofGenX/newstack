use strict;
use warnings;

use ExtUtils::MakeMaker;

WriteMakefile(
    NAME             => 'CsvQuery',
    VERSION_FROM     => 'lib/CsvQuery.pm',
    ABSTRACT         => 'CSV query tool',
    LICENSE          => 'mit',
    MIN_PERL_VERSION => '5.010',
    EXE_FILES        => ['bin/{{ npm_name }}'],
    PREREQ_PM        => { 'Test::More' => 0 },
    TEST_REQUIRES    => { 'Test::More' => 0 },
    test             => { TESTS => 't/*.t' },
);

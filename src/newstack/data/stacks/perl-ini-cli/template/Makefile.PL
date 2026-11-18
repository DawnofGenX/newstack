use strict;
use warnings;

use ExtUtils::MakeMaker;

WriteMakefile(
    NAME             => 'IniLite',
    VERSION_FROM     => 'lib/IniLite.pm',
    ABSTRACT         => 'A small INI reader with sections, lookups and JSON output',
    LICENSE          => 'mit',
    MIN_PERL_VERSION => '5.010',
    EXE_FILES        => ['bin/{{ npm_name }}'],
    PREREQ_PM        => { 'Test::More' => 0, 'JSON::PP' => 0 },
    TEST_REQUIRES    => { 'Test::More' => 0 },
    test             => { TESTS => 't/*.t' },
);

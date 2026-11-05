<?php

declare(strict_types=1);

namespace Tests\Unit;

use App\Support\TextStat;
use PHPUnit\Framework\TestCase;

final class TextStatTest extends TestCase
{
    public function test_empty_text_counts_as_zero(): void
    {
        self::assertSame(['lines' => 0, 'words' => 0, 'bytes' => 0], TextStat::of(''));
    }

    public function test_lines_are_newline_characters_like_wc(): void
    {
        // `wc -l` counts newlines, so text without a trailing one reports one
        // line fewer than the number of lines a human sees.
        self::assertSame(2, TextStat::of("one\ntwo\n")['lines']);
        self::assertSame(1, TextStat::of("one\ntwo")['lines']);
        self::assertSame(0, TextStat::of('one')['lines']);
    }

    public function test_words_are_runs_of_non_whitespace(): void
    {
        self::assertSame(3, TextStat::of("one\ttwo   three")['words']);
        self::assertSame(0, TextStat::of(" \n\t ")['words']);
    }

    public function test_bytes_are_raw_string_length_not_characters(): void
    {
        $stats = TextStat::of('héllo');

        self::assertSame(1, $stats['words']);
        self::assertSame(6, $stats['bytes']);
    }
}

<?php
declare(strict_types=1);

namespace {{ package_name }}\Tests;

use {{ package_name }}\Csv;
use {{ package_name }}\Report;
use PHPUnit\Framework\TestCase;

final class CsvTest extends TestCase
{
    private string $sample = "name,dept,score\nalice,eng,10\nbob,eng,20\ncarol,sales,5\n";

    public function testParsesRowsAndHeaders(): void
    {
        $t = Csv::parse($this->sample);
        $this->assertSame(['name', 'dept', 'score'], $t['headers']);
        $this->assertCount(3, $t['rows']);
    }

    public function testGroupCount(): void
    {
        $t = Csv::parse($this->sample);
        $this->assertSame(['eng' => 2, 'sales' => 1], Report::groupCount($t, 'dept'));
    }

    public function testSumColumn(): void
    {
        $t = Csv::parse($this->sample);
        $this->assertEquals(35.0, Report::sum($t, 'score'));
    }

    public function testQuotedFields(): void
    {
        $t = Csv::parse("a,b\n\"x,y\",2\n");
        $this->assertSame(['x,y', '2'], $t['rows'][0]);
    }
}
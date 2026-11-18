<?php
declare(strict_types=1);

namespace {{ package_name }};

final class Report
{
    public static function indexOf(array $table, string $column): int
    {
        $idx = array_search($column, $table['headers'], true);
        if ($idx === false) {
            throw new \InvalidArgumentException("unknown column: $column");
        }
        return (int) $idx;
    }

    /** @return array<string,int> */
    public static function groupCount(array $table, string $column): array
    {
        $idx = self::indexOf($table, $column);
        $counts = [];
        foreach ($table['rows'] as $row) {
            $key = (string) ($row[$idx] ?? '');
            $counts[$key] = ($counts[$key] ?? 0) + 1;
        }
        ksort($counts);
        return $counts;
    }

    public static function sum(array $table, string $column): float
    {
        $idx = self::indexOf($table, $column);
        $total = 0.0;
        foreach ($table['rows'] as $row) {
            $total += (float) ($row[$idx] ?? 0);
        }
        return $total;
    }
}
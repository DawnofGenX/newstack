<?php
declare(strict_types=1);

// php-csv-report

namespace {{ package_name }};

final class Csv
{
    /**
     * @return array{headers: list<string>, rows: list<list<string>>}
     */
    public static function parse(string $text): array
    {
        $lines = preg_split('/\r\n|\r|\n/', trim($text)) ?: [];
        $lines = array_values(array_filter($lines, static fn ($l) => trim($l) !== '', ARRAY_FILTER_USE_BOTH));
        if ($lines === []) {
            return ['headers' => [], 'rows' => []];
        }
        $rows = array_map([self::class, 'parseLine'], $lines);
        $headers = $rows[0];
        array_shift($rows);
        return ['headers' => $headers, 'rows' => array_values($rows)];
    }

    /** @return list<string> */
    private static function parseLine(string $line): array
    {
        $fields = [];
        $sb = '';
        $inQuotes = false;
        $len = strlen($line);
        for ($i = 0; $i < $len; $i++) {
            $c = $line[$i];
            if ($c === '"') {
                if ($inQuotes && $i + 1 < $len && $line[$i + 1] === '"') {
                    $sb .= '"';
                    $i++;
                } else {
                    $inQuotes = !$inQuotes;
                }
            } elseif ($c === ',' && !$inQuotes) {
                $fields[] = $sb;
                $sb = '';
            } else {
                $sb .= $c;
            }
        }
        $fields[] = $sb;
        return $fields;
    }

    public static function readFile(string $path): array
    {
        $text = file_get_contents($path);
        if ($text === false) {
            throw new \RuntimeException("cannot read $path");
        }
        return self::parse($text);
    }
}
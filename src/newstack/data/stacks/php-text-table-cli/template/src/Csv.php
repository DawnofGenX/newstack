<?php

declare(strict_types=1);

namespace {{ package_name }};

/** RFC 4180 reading and writing: quotes are doubled, delimiters and newlines may be quoted. */
final class Csv
{
    /**
     * @return list<list<string>>
     */
    public static function parse(string $text, string $delimiter = ','): array
    {
        if (strlen($delimiter) !== 1) {
            throw new \InvalidArgumentException('delimiter must be a single character');
        }

        $rows = [];
        $row = [];
        $field = '';
        $inQuotes = false;
        $length = strlen($text);

        for ($i = 0; $i < $length; $i += 1) {
            $char = $text[$i];

            if ($inQuotes) {
                if ($char === '"') {
                    if ($i + 1 < $length && $text[$i + 1] === '"') {
                        $field .= '"';
                        $i += 1;
                        continue;
                    }
                    $inQuotes = false;
                    continue;
                }
                $field .= $char;
                continue;
            }

            if ($char === '"' && $field === '') {
                $inQuotes = true;
                continue;
            }

            if ($char === $delimiter) {
                $row[] = $field;
                $field = '';
                continue;
            }

            if ($char === "\r") {
                continue;
            }

            if ($char === "\n") {
                $row[] = $field;
                $rows[] = $row;
                $row = [];
                $field = '';
                continue;
            }

            $field .= $char;
        }

        if ($inQuotes) {
            throw new \InvalidArgumentException('unterminated quoted field');
        }

        if ($field !== '' || $row !== []) {
            $row[] = $field;
            $rows[] = $row;
        }

        return $rows;
    }

    /**
     * @param list<list<string>> $rows
     */
    public static function render(array $rows, string $delimiter = ','): string
    {
        $lines = [];
        foreach ($rows as $row) {
            $cells = array_map(static function (string $cell) use ($delimiter): string {
                $needsQuotes = str_contains($cell, $delimiter)
                    || str_contains($cell, '"')
                    || str_contains($cell, "\n")
                    || str_contains($cell, "\r");
                return $needsQuotes ? '"' . str_replace('"', '""', $cell) . '"' : $cell;
            }, $row);
            $lines[] = implode($delimiter, $cells);
        }

        return $lines === [] ? '' : implode("\n", $lines) . "\n";
    }
}

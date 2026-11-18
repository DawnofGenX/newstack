<?php

declare(strict_types=1);

namespace {{ package_name }};

/**
 * Renders rows as an aligned text table. Width is measured with mb_strwidth, so
 * a double-width character (most CJK) counts as two columns and the borders
 * still line up.
 */
final class Table
{
    public const ALIGN_LEFT = 'left';

    public const ALIGN_RIGHT = 'right';

    public const ALIGN_CENTER = 'center';

    public const BORDER_ASCII = 'ascii';

    public const BORDER_UNICODE = 'unicode';

    public const BORDER_NONE = 'none';

    /** @var list<list<string>> */
    private array $rows = [];

    /** @var list<string>|null */
    private ?array $headers = null;

    /** @var list<string> */
    private array $alignments = [];

    private string $border = self::BORDER_ASCII;

    private int $maxWidth = 0;

    /**
     * @param list<list<string>> $rows
     * @param list<string>|null  $headers
     */
    public static function make(array $rows, ?array $headers = null): self
    {
        $table = new self();
        $table->rows = array_values($rows);
        $table->headers = $headers === null ? null : array_values($headers);

        return $table;
    }

    public function border(string $border): self
    {
        if (!in_array($border, [self::BORDER_ASCII, self::BORDER_UNICODE, self::BORDER_NONE], true)) {
            throw new \InvalidArgumentException("unknown border style: {$border}");
        }
        $this->border = $border;

        return $this;
    }

    /** @param list<string> $alignments */
    public function alignments(array $alignments): self
    {
        foreach ($alignments as $alignment) {
            if (!in_array($alignment, [self::ALIGN_LEFT, self::ALIGN_RIGHT, self::ALIGN_CENTER], true)) {
                throw new \InvalidArgumentException("unknown alignment: {$alignment}");
            }
        }
        $this->alignments = array_values($alignments);

        return $this;
    }

    /** Truncates every cell to this many characters, appending an ellipsis. */
    public function maxWidth(int $maxWidth): self
    {
        if ($maxWidth < 0) {
            throw new \InvalidArgumentException('max width cannot be negative');
        }
        $this->maxWidth = $maxWidth;

        return $this;
    }

    public function render(): string
    {
        $rows = $this->rows;
        if ($this->maxWidth > 0) {
            $rows = array_map(fn (array $row): array => array_map(fn (string $cell): string => $this->truncate($cell), $row), $rows);
        }

        $headers = $this->headers;
        if ($headers !== null && $this->maxWidth > 0) {
            $headers = array_map(fn (string $cell): string => $this->truncate($cell), $headers);
        }

        $columns = 0;
        foreach (array_merge($headers === null ? [] : [$headers], $rows) as $row) {
            $columns = max($columns, count($row));
        }

        if ($columns === 0) {
            return '';
        }

        $widths = array_fill(0, $columns, 0);
        foreach ($this->paddedRows($rows, $headers, $columns) as $row) {
            foreach ($row as $index => $cell) {
                $widths[$index] = max($widths[$index], mb_strwidth($cell, 'UTF-8'));
            }
        }

        $alignments = $this->alignments === []
            ? array_fill(0, $columns, self::ALIGN_LEFT)
            : array_pad($this->alignments, $columns, self::ALIGN_LEFT);

        $lines = [];

        if ($this->border !== self::BORDER_NONE) {
            $lines[] = $this->rule($widths, 'top');
        }

        if ($headers !== null) {
            $lines[] = $this->line(array_pad($headers, $columns, ''), $widths, $alignments);
            if ($this->border !== self::BORDER_NONE) {
                $lines[] = $this->rule($widths, 'middle');
            }
        }

        foreach ($rows as $row) {
            $lines[] = $this->line(array_pad($row, $columns, ''), $widths, $alignments);
        }

        if ($this->border !== self::BORDER_NONE) {
            $lines[] = $this->rule($widths, 'bottom');
        }

        return implode("\n", $lines) . "\n";
    }

    /**
     * @param list<list<string>> $rows
     * @param list<string>|null  $headers
     *
     * @return list<list<string>>
     */
    private function paddedRows(array $rows, ?array $headers, int $columns): array
    {
        $all = $headers === null ? $rows : array_merge([$headers], $rows);

        return array_map(static fn (array $row): array => array_pad($row, $columns, ''), $all);
    }

    private function truncate(string $cell): string
    {
        if (mb_strwidth($cell, 'UTF-8') <= $this->maxWidth) {
            return $cell;
        }
        if ($this->maxWidth <= 1) {
            return mb_substr($cell, 0, $this->maxWidth, 'UTF-8');
        }

        return mb_substr($cell, 0, $this->maxWidth - 1, 'UTF-8') . '…';
    }

    /**
     * @param list<string> $cells
     * @param list<int>    $widths
     * @param list<string> $alignments
     */
    private function line(array $cells, array $widths, array $alignments): string
    {
        [$left, $middle, $right] = $this->edges();
        $rendered = [];
        foreach ($cells as $index => $cell) {
            $rendered[] = $this->pad($cell, $widths[$index] ?? 0, $alignments[$index] ?? self::ALIGN_LEFT);
        }

        if ($this->border === self::BORDER_NONE) {
            // With no borders the last column needs no padding at all.
            return rtrim(implode('  ', $rendered));
        }

        $body = implode(" {$middle} ", $rendered);

        return $left . ' ' . $body . ' ' . $right;
    }

    /**
     * @param list<int>                    $widths
     * @param 'top'|'middle'|'bottom'      $kind
     */
    private function rule(array $widths, string $kind): string
    {
        if ($this->border === self::BORDER_NONE) {
            return '';
        }

        if ($this->border === self::BORDER_UNICODE) {
            [$left, $join, $right] = match ($kind) {
                'top' => ['┌', '┬', '┐'],
                'bottom' => ['└', '┴', '┘'],
                default => ['├', '┼', '┤'],
            };

            return $left . implode($join, array_map(static fn (int $width): string => str_repeat('─', $width + 2), $widths)) . $right;
        }

        return '+' . implode('+', array_map(static fn (int $width): string => str_repeat('-', $width + 2), $widths)) . '+';
    }

    /** @return array{0: string, 1: string, 2: string} */
    private function edges(): array
    {
        if ($this->border === self::BORDER_UNICODE) {
            return ['│', '│', '│'];
        }

        return ['|', '|', '|'];
    }

    private function pad(string $cell, int $width, string $alignment): string
    {
        $padding = max(0, $width - mb_strwidth($cell, 'UTF-8'));
        if ($alignment === self::ALIGN_RIGHT) {
            return str_repeat(' ', $padding) . $cell;
        }
        if ($alignment === self::ALIGN_CENTER) {
            $left = intdiv($padding, 2);

            return str_repeat(' ', $left) . $cell . str_repeat(' ', $padding - $left);
        }

        return $cell . str_repeat(' ', $padding);
    }
}

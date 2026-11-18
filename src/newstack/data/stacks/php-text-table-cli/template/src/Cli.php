<?php

declare(strict_types=1);

namespace {{ package_name }};

use InvalidArgumentException;
use Throwable;

/** argv handling: reads CSV from a file or stdin and renders it as a table. */
final class Cli
{
    public function __construct(private readonly string $program)
    {
    }

    /**
     * @param list<string>       $argv
     * @param resource           $stdin
     * @param resource           $stdout
     * @param resource           $stderr
     */
    public function run(array $argv, $stdin, $stdout, $stderr): int
    {
        $delimiter = ',';
        $border = Table::BORDER_ASCII;
        $align = Table::ALIGN_LEFT;
        $alignments = [];
        $maxWidth = 0;
        $hasHeader = false;
        $file = null;

        for ($i = 0; $i < count($argv); $i += 1) {
            $arg = $argv[$i];
            switch ($arg) {
                case '-h':
                case '--help':
                    fwrite($stdout, $this->usage());

                    return 0;
                case '-d':
                case '--delimiter':
                    $delimiter = $this->value($argv, $i, $stderr, 'delimiter');
                    if ($delimiter === null) {
                        return 2;
                    }
                    break;
                case '-b':
                case '--border':
                    $border = $this->value($argv, $i, $stderr, 'border');
                    if ($border === null) {
                        return 2;
                    }
                    break;
                case '-a':
                case '--align':
                    $align = $this->value($argv, $i, $stderr, 'align');
                    if ($align === null) {
                        return 2;
                    }
                    break;
                case '--align-column':
                    $spec = $this->value($argv, $i, $stderr, 'align-column');
                    if ($spec === null) {
                        return 2;
                    }
                    $parts = explode('=', $spec, 2);
                    if (count($parts) !== 2) {
                        fwrite($stderr, "{$this->program}: --align-column wants COLUMN=ALIGNMENT\n");

                        return 2;
                    }
                    if (!in_array($parts[1], [Table::ALIGN_LEFT, Table::ALIGN_RIGHT, Table::ALIGN_CENTER], true)) {
                        fwrite($stderr, "{$this->program}: unknown alignment {$parts[1]}\n");

                        return 2;
                    }
                    $alignments[(int) $parts[0]] = $parts[1];
                    break;
                case '-w':
                case '--max-width':
                    $raw = $this->value($argv, $i, $stderr, 'max-width');
                    if ($raw === null) {
                        return 2;
                    }
                    $maxWidth = (int) $raw;
                    break;
                case '--header':
                    $hasHeader = true;
                    break;
                default:
                    if (str_starts_with($arg, '-') && $arg !== '-') {
                        fwrite($stderr, "{$this->program}: unknown option {$arg}\n");

                        return 2;
                    }
                    if ($file !== null) {
                        fwrite($stderr, "{$this->program}: expected at most one file\n");

                        return 2;
                    }
                    $file = $arg;
            }
        }

        if ($delimiter === 'tab' || $delimiter === '\\t') {
            $delimiter = "\t";
        }

        $text = '';
        if ($file === null || $file === '-') {
            $text = (string) stream_get_contents($stdin);
        } else {
            $content = @file_get_contents($file);
            if ($content === false) {
                fwrite($stderr, "{$this->program}: cannot read {$file}\n");

                return 1;
            }
            $text = $content;
        }

        try {
            $rows = Csv::parse($text, $delimiter);
            if ($rows === []) {
                fwrite($stderr, "{$this->program}: no rows\n");

                return 1;
            }

            $headers = null;
            if ($hasHeader) {
                $headers = array_shift($rows);
            }

            $table = Table::make($rows, $headers)
                ->border($border)
                ->maxWidth($maxWidth);
            if ($alignments !== []) {
                // Spell every column out: the map is sparse and its keys are
                // column indexes, which the renderer must not renumber.
                $dense = array_fill(0, max(1, count($headers ?? $rows[0])), Table::ALIGN_LEFT);
                foreach ($alignments as $index => $value) {
                    $dense[$index] = $value;
                }
                $table = $table->alignments($dense);
            } elseif ($align !== Table::ALIGN_LEFT) {
                $table = $table->alignments(array_fill(0, max(1, count($headers ?? $rows[0])), $align));
            }

            fwrite($stdout, $table->render());

            return 0;
        } catch (InvalidArgumentException $error) {
            fwrite($stderr, "{$this->program}: {$error->getMessage()}\n");

            return 1;
        } catch (Throwable $error) {
            fwrite($stderr, "{$this->program}: {$error->getMessage()}\n");

            return 1;
        }
    }

    /**
     * @param list<string> $argv
     * @param resource     $stderr
     */
    private function value(array $argv, int &$index, $stderr, string $name): ?string
    {
        $value = $argv[$index + 1] ?? null;
        if ($value === null) {
            fwrite($stderr, "{$this->program}: --{$name} needs a value\n");

            return null;
        }
        $index += 1;

        return $value;
    }

    private function usage(): string
    {
        return <<<TXT
        {$this->program} — render CSV as an aligned text table

        Usage:
          {$this->program} [options] [FILE]

        Reads FILE, or stdin when FILE is missing or "-".

        Options:
          -d, --delimiter CHAR     field separator (default ",", "tab" accepted)
          -b, --border STYLE       ascii, unicode or none (default ascii)
          -a, --align ALIGN        left, right or center for every column
              --align-column C=A   alignment for one 0-based column; repeatable
          -w, --max-width N        truncate cells to N characters with an ellipsis
              --header             treat the first row as a header
          -h, --help               show this help

        TXT;
    }
}

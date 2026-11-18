<?php

declare(strict_types=1);

namespace {{ package_name }};

use Throwable;

/**
 * argv -> exit code. Reads JSON for `encode` and bencode for `decode`, so the
 * tool composes with the rest of a JSON pipeline.
 */
final class Cli
{
    private const USAGE = <<<'TEXT'
        Usage: {program} COMMAND [FILE]

        Bencode encoder/decoder (the BitTorrent encoding).

        Commands:
          encode [FILE]   read JSON and write bencode (FILE omitted or '-' reads stdin)
          decode [FILE]   read bencode and write JSON

        Exit codes:
          0  success
          1  the input was not valid JSON / bencode, or the file was unreadable
          2  usage error
        TEXT;

    public function __construct(private readonly string $program = '{{ npm_name }}')
    {
    }

    /**
     * @param list<string> $argv arguments after the program name
     * @param resource $stdin
     * @param resource $stdout
     * @param resource $stderr
     */
    public function run(array $argv, $stdin, $stdout, $stderr): int
    {
        $command = array_shift($argv);

        if ($command === null) {
            return $this->usage($stderr, 'a command is required');
        }

        if ($command === '-h' || $command === '--help') {
            fwrite($stdout, str_replace('{program}', $this->program, self::USAGE) . PHP_EOL);

            return 0;
        }

        if ($command !== 'encode' && $command !== 'decode') {
            return $this->usage($stderr, "unknown command: {$command}");
        }

        if (count($argv) > 1) {
            return $this->usage($stderr, 'that command takes at most one path');
        }

        $path = $argv[0] ?? '-';
        if ($path === '-') {
            $input = stream_get_contents($stdin);
            if ($input === false) {
                $input = '';
            }
        } else {
            if (!is_file($path)) {
                fwrite($stderr, "{$this->program}: cannot read {$path}" . PHP_EOL);

                return 1;
            }
            $input = (string) file_get_contents($path);
        }

        try {
            if ($command === 'encode') {
                $decoded = json_decode($input, true, 512, JSON_THROW_ON_ERROR);
                fwrite($stdout, Bencode::encode($decoded) . PHP_EOL);
            } else {
                $value = Bencode::decode(trim($input));
                fwrite($stdout, json_encode($value, JSON_UNESCAPED_SLASHES | JSON_THROW_ON_ERROR) . PHP_EOL);
            }
        } catch (Throwable $error) {
            fwrite($stderr, "{$this->program}: " . $error->getMessage() . PHP_EOL);

            return 1;
        }

        return 0;
    }

    /** @param resource $stderr */
    private function usage($stderr, string $message): int
    {
        fwrite($stderr, "{$this->program}: {$message}" . PHP_EOL);
        fwrite($stderr, str_replace('{program}', $this->program, self::USAGE) . PHP_EOL);

        return 2;
    }
}

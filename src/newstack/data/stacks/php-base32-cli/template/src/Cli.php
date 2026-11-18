<?php

declare(strict_types=1);

namespace {{ package_name }};

use InvalidArgumentException;

final class Cli
{
    public function __construct(private readonly string $program)
    {
    }

    /**
     * @param list<string> $arguments
     * @param resource $stdin
     * @param resource $stdout
     * @param resource $stderr
     */
    public function run(array $arguments, $stdin, $stdout, $stderr): int
    {
        $command = $arguments[0] ?? null;
        if ($command === null || $command === '--help' || $command === '-h') {
            fwrite($stdout, $this->usage());

            return 0;
        }
        if (!in_array($command, ['encode', 'decode'], true)) {
            fwrite($stderr, sprintf('error: unknown command %s%s', $command, PHP_EOL));
            fwrite($stderr, $this->usage());

            return 2;
        }

        $crockford = false;
        $noPad = false;
        $path = null;
        foreach (array_slice($arguments, 1) as $argument) {
            if ($argument === '--crockford') {
                $crockford = true;
            } elseif ($argument === '--no-pad') {
                $noPad = true;
            } elseif (str_starts_with($argument, '-') && $argument !== '-') {
                fwrite($stderr, sprintf('error: unknown option %s%s', $argument, PHP_EOL));
                fwrite($stderr, $this->usage());

                return 2;
            } else {
                $path = $argument;
            }
        }

        $input = $this->read($path, $stdin);
        if ($input === null) {
            fwrite($stderr, sprintf('error: cannot read %s%s', $path ?? 'stdin', PHP_EOL));

            return 1;
        }

        try {
            if ($command === 'encode') {
                $output = $crockford
                    ? Base32::encodeCrockford($input)
                    : Base32::encode($input, !$noPad);
            } else {
                $output = $crockford ? Base32::decodeCrockford($input) : Base32::decode($input);
            }
        } catch (InvalidArgumentException $error) {
            fwrite($stderr, 'error: ' . $error->getMessage() . PHP_EOL);

            return 1;
        }

        fwrite($stdout, $output . PHP_EOL);

        return 0;
    }

    private function usage(): string
    {
        return implode(PHP_EOL, [
            sprintf('usage: %s encode|decode [--crockford] [--no-pad] [FILE]', $this->program),
            '',
            '  encode   base32 encode stdin, or FILE when given',
            '  decode   base32 decode stdin, or FILE when given',
            '',
            '  --crockford  use the Crockford alphabet (0-9A-Z without I, L, O, U)',
            '  --no-pad     omit = padding when encoding',
            '  FILE         read from FILE instead of stdin, or - for stdin',
            '',
        ]);
    }

    /**
     * @param resource $stdin
     */
    private function read(?string $path, $stdin): ?string
    {
        if ($path === null || $path === '-') {
            $contents = stream_get_contents($stdin);

            return $contents === false ? null : $contents;
        }
        if (!is_file($path)) {
            return null;
        }
        $contents = file_get_contents($path);

        return $contents === false ? null : $contents;
    }
}

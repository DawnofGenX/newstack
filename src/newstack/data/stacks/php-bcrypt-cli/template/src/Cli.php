<?php

declare(strict_types=1);

namespace {{ package_name }};

use InvalidArgumentException;
use Throwable;

final class Cli
{
    public function __construct(private readonly string $program)
    {
    }

    /**
     * @param list<string> $argv
     */
    public function run(array $argv, $stdin, $stdout, $stderr): int
    {
        if ($argv === []) {
            fwrite($stderr, "{$this->program}: no command given\n");

            return 2;
        }
        if (in_array($argv[0], ['-h', '--help'], true)) {
            fwrite($stdout, $this->usage());

            return 0;
        }

        $command = $argv[0];
        $rest = array_slice($argv, 1);

        try {
            switch ($command) {
                case 'hash':
                    if (count($rest) < 1 || count($rest) > 2) {
                        throw new InvalidArgumentException('hash needs PASSWORD [COST]');
                    }
                    $cost = count($rest) === 2 ? (int) $rest[1] : Bcrypt::DEFAULT_COST;
                    $hash = Bcrypt::hash($rest[0], $cost);
                    fwrite($stdout, $hash . "\n");

                    return 0;
                case 'verify':
                    if (count($rest) !== 2) {
                        throw new InvalidArgumentException('verify needs PASSWORD HASH');
                    }
                    $ok = Bcrypt::verify($rest[0], $rest[1]);
                    fwrite($stdout, ($ok ? 'match' : 'mismatch') . "\n");

                    return $ok ? 0 : 1;
                default:
                    fwrite($stderr, "{$this->program}: unknown command {$command}\n");

                    return 2;
            }
        } catch (InvalidArgumentException $error) {
            fwrite($stderr, "{$this->program}: {$error->getMessage()}\n");

            return 2;
        } catch (Throwable $error) {
            fwrite($stderr, "{$this->program}: {$error->getMessage()}\n");

            return 1;
        }
    }

    private function usage(): string
    {
        return <<<TXT
{$this->program} — bcrypt password hashing and verification

Usage:
  {$this->program} hash PASSWORD [COST]
  {$this->program} verify PASSWORD HASH

Exit codes: 0 success, 1 bad input or mismatch, 2 usage error.

TXT;
    }
}
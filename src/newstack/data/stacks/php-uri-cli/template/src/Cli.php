<?php

declare(strict_types=1);

namespace {{ package_name }};

use InvalidArgumentException;
use Throwable;

/**
 * The command line: arguments in, text out, an exit code returned. The streams
 * and the program name are injected so the tests never spawn a process.
 */
final class Cli
{
    public const USAGE = <<<'TEXT'
        usage: %s COMMAND [ARGUMENTS]

        Work with RFC 3986 URI components.

          parse URI                 print the components as JSON
          normalize URI             lowercase scheme and host, drop the default
                                    port, resolve dot segments, keep a path of /
          encode VALUE              percent-encode a value for a path or query
          decode VALUE              percent-decode a value
          query URI KEY=VALUE ...   replace or add query parameters

        Arguments:
          -h, --help                show this help and exit

        Exit codes: 0 success, 1 bad input, 2 usage error.
        TEXT;

    public function __construct(private readonly string $program)
    {
    }

    /**
     * @param list<string> $argv
     * @param resource $stdin
     * @param resource $stdout
     * @param resource $stderr
     */
    public function run(array $argv, $stdin, $stdout, $stderr): int
    {
        try {
            if ($argv === [] || $argv[0] === '-h' || $argv[0] === '--help') {
                if ($argv !== []) {
                    fwrite($stdout, sprintf(self::USAGE, $this->program) . PHP_EOL);

                    return 0;
                }
                throw new InvalidArgumentException('no command given');
            }

            $command = array_shift($argv);
            $output = match ($command) {
                'parse' => $this->parseCommand($argv),
                'normalize' => Uri::normalize($this->one($argv, $command)),
                'encode' => rawurlencode($this->one($argv, $command)),
                'decode' => rawurldecode($this->one($argv, $command)),
                'query' => $this->queryCommand($argv),
                default => throw new InvalidArgumentException('unknown command: ' . $command),
            };

            fwrite($stdout, $output . PHP_EOL);

            return 0;
        } catch (InvalidArgumentException $error) {
            fwrite($stderr, 'error: ' . $error->getMessage() . PHP_EOL);
            fwrite($stderr, PHP_EOL . sprintf(self::USAGE, $this->program) . PHP_EOL);

            return 2;
        } catch (Throwable $error) {
            fwrite($stderr, 'error: ' . $error->getMessage() . PHP_EOL);

            return 1;
        }
    }

    /** @param list<string> $argv */
    private function parseCommand(array $argv): string
    {
        $parts = Uri::parse($this->one($argv, 'parse'));
        $json = json_encode($parts, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE);
        if ($json === false) {
            throw new InvalidArgumentException('cannot encode the components as JSON');
        }

        return $json;
    }

    /** @param list<string> $argv */
    private function queryCommand(array $argv): string
    {
        if (count($argv) < 2) {
            throw new InvalidArgumentException('query needs a URI and at least one KEY=VALUE');
        }
        $uri = array_shift($argv);
        $replacements = [];
        foreach ($argv as $pair) {
            if (!str_contains($pair, '=')) {
                throw new InvalidArgumentException('expected KEY=VALUE, got: ' . $pair);
            }
            [$key, $value] = explode('=', $pair, 2);
            if ($key === '') {
                throw new InvalidArgumentException('a query key cannot be empty');
            }
            $replacements[$key] = $value;
        }

        $parts = Uri::parse($uri);
        $pairs = Uri::mergeQuery(Uri::queryPairs($parts['query'] ?? ''), $replacements);
        $parts['query'] = Uri::encodeQuery($pairs);

        return Uri::toString($parts);
    }

    /**
     * @param list<string> $argv
     */
    private function one(array $argv, string $command): string
    {
        if (count($argv) !== 1) {
            throw new InvalidArgumentException($command . ' takes exactly one argument');
        }

        return $argv[0];
    }
}

<?php

declare(strict_types=1);

namespace {{ package_name }};

use JsonException;
use Throwable;

/** The command line front end: get, set, remove, has, tokens. */
final class Cli
{
    public function __construct(private readonly string $program)
    {
    }

    /**
     * @param list<string> $args
     * @param resource $stdin
     * @param resource $stdout
     * @param resource $stderr
     */
    public function run(array $args, $stdin, $stdout, $stderr): int
    {
        $usage = $this->usage();
        if ($args === [] || $args[0] === '-h' || $args[0] === '--help') {
            fwrite($stdout, $usage);

            return $args === [] ? 2 : 0;
        }

        $command = array_shift($args);
        if (!in_array($command, ['get', 'set', 'remove', 'has', 'tokens'], true)) {
            fwrite($stderr, sprintf("%s: unknown command %s%s", $this->program, $command, PHP_EOL));

            return 2;
        }

        $pointer = null;
        $files = [];
        $value = null;
        $hasValue = false;
        for ($index = 0; $index < count($args); $index++) {
            $argument = $args[$index];
            if ($argument === '-v' || $argument === '--value') {
                if (!array_key_exists($index + 1, $args)) {
                    fwrite($stderr, sprintf("%s: --value needs a JSON value%s", $this->program, PHP_EOL));

                    return 2;
                }
                $value = $args[++$index];
                $hasValue = true;
            } elseif ($argument === '-h' || $argument === '--help') {
                fwrite($stdout, $usage);

                return 0;
            } elseif ($argument !== '-' && str_starts_with($argument, '-')) {
                fwrite($stderr, sprintf("%s: unknown option %s%s", $this->program, $argument, PHP_EOL));

                return 2;
            } elseif ($pointer === null) {
                $pointer = $argument;
            } else {
                $files[] = $argument;
            }
        }

        $pointer ??= '';
        try {
            $text = $files === [] ? stream_get_contents($stdin) : file_get_contents($files[0]);
        } catch (Throwable $error) {
            fwrite($stderr, sprintf('%s: %s%s', $this->program, $error->getMessage(), PHP_EOL));

            return 1;
        }
        if ($text === false) {
            fwrite($stderr, sprintf("%s: cannot read %s%s", $this->program, $files[0], PHP_EOL));

            return 1;
        }

        try {
            $document = $this->decode($text);
        } catch (JsonException $error) {
            fwrite($stderr, sprintf('%s: invalid JSON: %s%s', $this->program, $error->getMessage(), PHP_EOL));

            return 1;
        }

        try {
            switch ($command) {
                case 'tokens':
                    fwrite($stdout, json_encode(JsonPointer::tokens($pointer), JSON_UNESCAPED_SLASHES) . PHP_EOL);

                    return 0;
                case 'has':
                    return JsonPointer::exists($document, $pointer) ? 0 : 1;
                case 'get':
                    $found = JsonPointer::get($document, $pointer);
                    fwrite($stdout, json_encode($found, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE) . PHP_EOL);

                    return 0;
                case 'set':
                    if (!$hasValue) {
                        fwrite($stderr, sprintf("%s: set needs --value%s", $this->program, PHP_EOL));

                        return 2;
                    }
                    JsonPointer::set($document, $pointer, $this->decode($value));
                    fwrite($stdout, json_encode($document, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE) . PHP_EOL);

                    return 0;
                default:
                    $removed = JsonPointer::remove($document, $pointer);
                    fwrite($stdout, json_encode(['removed' => $removed, 'document' => $document], JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE) . PHP_EOL);

                    return 0;
            }
        } catch (JsonPointerException $error) {
            fwrite($stderr, sprintf('%s: %s%s', $this->program, $error->getMessage(), PHP_EOL));

            return 1;
        }
    }

    private function decode(string $text): mixed
    {
        return json_decode($text, true, 512, JSON_THROW_ON_ERROR);
    }

    private function usage(): string
    {
        return <<<TEXT
            Usage: {$this->program} <command> [pointer] [file] [options]

            Commands:
              get POINTER     print the value at POINTER as JSON
              set POINTER     replace or insert the value given by --value
              remove POINTER  delete the value and print what was removed
              has POINTER     exit 0 when the pointer resolves, 1 otherwise
              tokens POINTER  print the decoded reference tokens

            Options:
              -v, --value JSON  the value for "set"
              -h, --help        show this message

            The document is read from FILE, or from stdin when no file is given.
            Unknown options exit 2, unreadable documents and unresolvable pointers
            exit 1.

            TEXT;
    }
}

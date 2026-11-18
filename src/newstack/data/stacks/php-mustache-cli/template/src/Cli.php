<?php

declare(strict_types=1);

namespace {{ package_name }};

use JsonException;
use Throwable;

/** Renders a Mustache template with JSON data from a file or standard input. */
final class Cli
{
    public function __construct(private readonly string $program) {}

    /**
     * @param list<string>   $args
     * @param resource       $stdin
     * @param resource       $stdout
     * @param resource       $stderr
     */
    public function run(array $args, $stdin, $stdout, $stderr): int
    {
        $templatePath = null;
        $dataPath = null;
        $inline = null;

        for ($index = 0; $index < count($args); $index++) {
            $arg = $args[$index];
            switch ($arg) {
                case '-h':
                case '--help':
                    fwrite($stdout, $this->usage());
                    return 0;
                case '--data':
                    $dataPath = $args[++$index] ?? null;
                    if ($dataPath === null) {
                        fwrite($stderr, "error: --data needs a file\n");
                        return 2;
                    }
                    break;
                case '--json':
                    $inline = $args[++$index] ?? null;
                    if ($inline === null) {
                        fwrite($stderr, "error: --json needs a value\n");
                        return 2;
                    }
                    break;
                default:
                    if (str_starts_with($arg, '-')) {
                        fwrite($stderr, "error: unknown option $arg\n");
                        fwrite($stderr, $this->usage());
                        return 2;
                    }
                    if ($templatePath !== null) {
                        fwrite($stderr, "error: only one template may be given\n");
                        return 2;
                    }
                    $templatePath = $arg;
                    break;
            }
        }

        try {
            $template = $templatePath === null
                ? (string) stream_get_contents($stdin)
                : $this->read($templatePath);
            $data = $inline !== null ? $this->decode($inline) : $this->decodeData($dataPath, $stdin);
            $rendered = (new Mustache())->render($template, $data);
        } catch (MustacheException $error) {
            fwrite($stderr, 'error: ' . $error->getMessage() . "\n");
            return 1;
        } catch (JsonException $error) {
            fwrite($stderr, 'error: invalid JSON: ' . $error->getMessage() . "\n");
            return 1;
        } catch (CliException $error) {
            fwrite($stderr, 'error: ' . $error->getMessage() . "\n");
            return 1;
        }

        fwrite($stdout, $rendered . (str_ends_with($rendered, "\n") ? '' : "\n"));
        return 0;
    }

    /** @return array<string, mixed> */
    private function decode(string $json): array
    {
        $data = json_decode($json, true, 64, JSON_THROW_ON_ERROR);
        if (!is_array($data)) {
            throw new CliException('the data must be a JSON object');
        }
        return $data;
    }

    /**
     * @param resource $stdin
     * @return array<string, mixed>
     */
    private function decodeData(?string $path, $stdin): array
    {
        if ($path !== null) {
            return $this->decode($this->read($path));
        }
        $piped = (string) stream_get_contents($stdin);
        return trim($piped) === '' ? [] : $this->decode($piped);
    }

    private function read(string $path): string
    {
        if (!is_file($path)) {
            throw new CliException("cannot read $path");
        }
        $contents = file_get_contents($path);
        if ($contents === false) {
            throw new CliException("cannot read $path");
        }
        return $contents;
    }

    private function usage(): string
    {
        return "usage: {$this->program} [TEMPLATE] [--data FILE] [--json OBJECT]\n\n"
            . "Renders a Mustache template. The template comes from the argument or\n"
            . "standard input; the data comes from --json, --data FILE or standard input\n"
            . "when the template is a file.\n\n"
            . "  {{!name}} escapes HTML, {{!{name}}} and {{!&name}} do not, {{!#list}} sections,\n"
            . "  {{!^name}} inverted sections and {{! comment}} are supported.\n\n"
            . "Exit status is 1 for a bad template or bad JSON and 2 for bad usage.\n";
    }
}

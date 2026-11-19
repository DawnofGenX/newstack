<?php
declare(strict_types=1);
namespace {{ package_name }};
use InvalidArgumentException;
use Throwable;
final class Cli
{
    public function __construct(private readonly string $program) {}
    public function run(array $argv, $stdin, $stdout, $stderr): int
    {
        if ($argv === []) { fwrite($stderr, "{$this->program}: no command given\n"); return 2; }
        if (in_array($argv[0], ['-h', '--help'], true)) { fwrite($stdout, $this->usage()); return 0; }
        $command = $argv[0];
        $rest = array_slice($argv, 1);
        try {
            switch ($command) {
                case 'format':
                    if (count($rest) < 1 || count($rest) > 2) throw new InvalidArgumentException('format needs AMOUNT [CURRENCY]');
                    $currency = count($rest) === 2 ? $rest[1] : 'USD';
                    $money = new Money($rest[0], $currency);
                    fwrite($stdout, $money->format() . "\n");
                    return 0;
                case 'allocate':
                    if (count($rest) !== 2) throw new InvalidArgumentException('allocate needs TOTAL PARTS');
                    $parts = Money::allocate((int) round(((float) $rest[0]) * 100), (int) $rest[1]);
                    fwrite($stdout, implode(',', array_map(fn (int $c): string => number_format($c / 100, 2, '.', ''), $parts)) . "\n");
                    return 0;
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
{$this->program} — money formatting and allocation
Usage:
  {$this->program} format AMOUNT [CURRENCY]
  {$this->program} allocate TOTAL PARTS
Exit codes: 0 success, 1 bad input, 2 usage error.
TXT;
    }
}

<?php
declare(strict_types=1);
namespace {{ package_name }};
final class Money
{
    public function __construct(private readonly string $amount, private readonly string $currency = 'USD') {}
    public function format(): string
    {
        $symbols = ['USD' => '$', 'EUR' => '€', 'GBP' => '£'];
        $symbol = $symbols[$this->currency] ?? $this->currency . ' ';
        return $symbol . number_format((float) $this->amount, 2, '.', ',');
    }
    public static function allocate(int $totalCents, int $parts): array
    {
        if ($parts <= 0) throw new \InvalidArgumentException('parts must be positive');
        $base = intdiv($totalCents, $parts);
        $remainder = $totalCents % $parts;
        $result = array_fill(0, $parts, $base);
        for ($i = 0; $i < $remainder; $i++) $result[$i] += 1;
        return $result;
    }
}

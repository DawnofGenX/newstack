<?php
declare(strict_types=1);

namespace {{ package_name }};

interface Clock
{
    public function now(): int;
}

final class SystemClock implements Clock
{
    public function now(): int
    {
        return time();
    }
}

final class FixedClock implements Clock
{
    public function __construct(private int $now) {}
    public function now(): int
    {
        return $this->now;
    }
    public function set(int $now): void
    {
        $this->now = $now;
    }
}

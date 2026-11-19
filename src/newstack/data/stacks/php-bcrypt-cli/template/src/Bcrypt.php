<?php

declare(strict_types=1);

namespace {{ package_name }};

/** bcrypt hashing and verification helpers. */
final class Bcrypt
{
    public const DEFAULT_COST = 10;

    public static function hash(string $password, int $cost = self::DEFAULT_COST): string
    {
        if ($cost < 4 || $cost > 31) {
            throw new \InvalidArgumentException('cost must be between 4 and 31');
        }
        $hash = password_hash($password, PASSWORD_BCRYPT, ['cost' => $cost]);
        if ($hash === false) {
            throw new \RuntimeException('password_hash failed');
        }
        return $hash;
    }

    public static function verify(string $password, string $hash): bool
    {
        return password_verify($password, $hash);
    }

    public static function needsRehash(string $hash, int $cost = self::DEFAULT_COST): bool
    {
        return password_needs_rehash($hash, PASSWORD_BCRYPT, ['cost' => $cost]);
    }
}
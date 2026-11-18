<?php

declare(strict_types=1);

namespace {{ package_name }};

/**
 * File-backed item store.
 *
 * PHP resets static properties at request shutdown, so neither the built-in
 * server nor php-fpm can keep an in-memory array alive between the POST that
 * adds an item and the GET that lists it. Persisting to a small JSON file keeps
 * the example dependency-free while behaving like a real service.
 */
final class Store
{
    public static function path(): string
    {
        $override = getenv('PHP_SLIM_ITEMS_FILE');

        return $override !== false && $override !== ''
            ? $override
            : sys_get_temp_dir() . '/php-slim-api-items.json';
    }

    public static function reset(): void
    {
        $path = self::path();
        if (is_file($path)) {
            unlink($path);
        }
    }

    /** @return string[] */
    public static function all(): array
    {
        $raw = self::read();
        if ($raw === null) {
            return [];
        }

        $decoded = json_decode($raw, true);
        if (!is_array($decoded)) {
            return [];
        }

        return array_values(array_filter($decoded, 'is_string'));
    }

    public static function add(string $name): void
    {
        $items = self::all();
        $items[] = $name;

        file_put_contents(self::path(), json_encode($items), LOCK_EX);
    }

    private static function read(): ?string
    {
        $path = self::path();
        if (!is_file($path)) {
            return null;
        }

        $raw = file_get_contents($path);
        if ($raw === false || trim($raw) === '') {
            return null;
        }

        return $raw;
    }
}

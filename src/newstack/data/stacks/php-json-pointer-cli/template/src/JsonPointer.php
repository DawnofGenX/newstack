<?php

declare(strict_types=1);

namespace {{ package_name }};

use RuntimeException;

/** Raised for malformed pointers and for paths that do not resolve. */
final class JsonPointerException extends RuntimeException
{
}

/**
 * RFC 6901 JSON Pointer over decoded JSON: get, set (add), remove, exists.
 *
 * A pointer is either the empty string (the whole document) or a sequence of
 * reference tokens separated by "/". "~1" encodes "/" and "~0" encodes "~",
 * in that order when decoding.
 */
final class JsonPointer
{
    /** @return list<string> */
    public static function tokens(string $pointer): array
    {
        if ($pointer === '') {
            return [];
        }
        if ($pointer[0] !== '/') {
            throw new JsonPointerException(sprintf("invalid pointer %s: must be empty or start with '/'", self::describe($pointer)));
        }

        $raw = explode('/', substr($pointer, 1));

        return array_map(static fn (string $token): string => self::unescape($token), $raw);
    }

    public static function escape(string $token): string
    {
        return str_replace(['~', '/'], ['~0', '~1'], $token);
    }

    public static function unescape(string $token): string
    {
        return str_replace(['~1', '~0'], ['/', '~'], $token);
    }

    public static function formatPath(array $tokens): string
    {
        if ($tokens === []) {
            return '(document root)';
        }

        return '/' . implode('/', array_map([self::class, 'escape'], $tokens));
    }

    public static function exists(mixed $document, string $pointer): bool
    {
        try {
            self::get($document, $pointer);

            return true;
        } catch (JsonPointerException) {
            return false;
        }
    }

    public static function get(mixed $document, string $pointer): mixed
    {
        $current = $document;
        $walked = [];
        foreach (self::tokens($pointer) as $token) {
            $walked[] = $token;
            $current = self::step($current, $token, self::formatPath($walked));
        }

        return $current;
    }

    /** RFC 6902 "add": replaces an existing member or inserts a new one. */
    public static function set(mixed &$document, string $pointer, mixed $value): void
    {
        $tokens = self::tokens($pointer);
        if ($tokens === []) {
            $document = $value;

            return;
        }
        $last = array_pop($tokens);
        $container = &self::reference($document, $tokens, self::formatPath($tokens), true);
        self::assign($container, $last, $value, self::formatPath(array_merge($tokens, [$last])));
    }

    public static function remove(mixed &$document, string $pointer): mixed
    {
        $tokens = self::tokens($pointer);
        if ($tokens === []) {
            throw new JsonPointerException('cannot remove the document root');
        }
        $last = array_pop($tokens);
        $container = &self::reference($document, $tokens, self::formatPath($tokens));
        $path = self::formatPath(array_merge($tokens, [$last]));

        if (is_array($container)) {
            if (!array_key_exists($last, $container)) {
                throw new JsonPointerException(sprintf('no such member %s at %s', self::describe($last), self::formatPath($tokens)));
            }
            $removed = $container[$last];
            $wasList = array_is_list($container);
            unset($container[$last]);
            if ($wasList) {
                $container = array_values($container);
            }

            return $removed;
        }

        throw new JsonPointerException(sprintf('cannot remove %s from a %s', $path, get_debug_type($container)));
    }

    private static function step(mixed $current, string $token, string $path): mixed
    {
        if (!is_array($current)) {
            throw new JsonPointerException(sprintf('cannot step into %s: it is a %s', $path === '/' . self::escape($token) ? '(document root)' : $path, get_debug_type($current)));
        }
        if (!array_key_exists($token, $current)) {
            throw new JsonPointerException(sprintf('no such member %s at %s', self::describe($token), $path === '/' . self::escape($token) ? '(document root)' : ''));
        }

        return $current[$token];
    }

    private static function &reference(mixed &$document, array $tokens, string $path, bool $create = false): mixed
    {
        $current = &$document;
        $walked = [];
        foreach ($tokens as $token) {
            $walked[] = $token;
            if (!is_array($current)) {
                throw new JsonPointerException(sprintf('cannot descend into %s: it is a %s', self::formatPath(array_slice($walked, 0, -1)), get_debug_type($current)));
            }
            if (!array_key_exists($token, $current)) {
                if (!$create || array_is_list($current)) {
                    throw new JsonPointerException(sprintf('no such member %s at %s', self::describe($token), self::formatPath($walked)));
                }
                $current[$token] = [];
            }
            $current = &$current[$token];
        }
        if (!is_array($current)) {
            throw new JsonPointerException(sprintf('cannot descend into %s: it is a %s', $path, get_debug_type($current)));
        }

        return $current;
    }

    private static function assign(mixed &$container, string $token, mixed $value, string $path): void
    {
        if (!is_array($container)) {
            throw new JsonPointerException(sprintf('cannot write %s into a %s', $path, get_debug_type($container)));
        }
        if ($container !== [] && array_is_list($container) && $token === '-') {
            $container[] = $value;

            return;
        }
        if ($container !== [] && array_is_list($container) && !preg_match('/^(0|[1-9][0-9]*)$/', $token)) {
            throw new JsonPointerException(sprintf('invalid array index %s for %s', self::describe($token), $path));
        }
        $container[$token] = $value;
    }

    private static function describe(string $token): string
    {
        return "'" . $token . "'";
    }
}

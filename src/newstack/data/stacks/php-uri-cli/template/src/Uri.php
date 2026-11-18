<?php

declare(strict_types=1);

namespace {{ package_name }};

use InvalidArgumentException;

/**
 * RFC 3986 URI components: parse, normalise and rebuild.
 *
 * The parsing regex is the one from RFC 3986 appendix B. Everything else here
 * is about the two things hand-written URI code usually gets wrong: the default
 * port (80 and 443 are not part of the identity) and dot segments (`/a/./b/../c`
 * is `/a/c`).
 */
final class Uri
{
    /** Default ports, which normalisation drops. */
    private const DEFAULT_PORTS = ['http' => 80, 'https' => 443, 'ftp' => 21];

    private const PATTERN = '~^(?:([^:/?#]+):)?(?://([^/?#]*))?([^?#]*)(?:\?([^#]*))?(?:#(.*))?$~s';

    /**
     * Splits a URI into its components. Missing components are null so a caller
     * can tell "no port" from "port 0".
     *
     * @return array{scheme: ?string, user: ?string, password: ?string, host: ?string, port: ?int, path: string, query: ?string, fragment: ?string}
     */
    public static function parse(string $uri): array
    {
        if (preg_match(self::PATTERN, $uri, $match) !== 1) {
            throw new InvalidArgumentException('cannot parse URI');
        }

        $scheme = ($match[1] ?? '') === '' ? null : strtolower($match[1]);
        $authority = $match[2] ?? null;
        $user = null;
        $password = null;
        $host = null;
        $port = null;

        if ($authority !== null) {
            $hostPart = $authority;
            $at = strrpos($authority, '@');
            if ($at !== false) {
                $userInfo = substr($authority, 0, $at);
                $hostPart = substr($authority, $at + 1);
                $colon = strpos($userInfo, ':');
                if ($colon === false) {
                    $user = rawurldecode($userInfo);
                } else {
                    $user = rawurldecode(substr($userInfo, 0, $colon));
                    $password = rawurldecode(substr($userInfo, $colon + 1));
                }
            }

            if ($hostPart !== '' && $hostPart[0] === '[') {
                $end = strpos($hostPart, ']');
                if ($end === false) {
                    throw new InvalidArgumentException('unterminated IPv6 literal');
                }
                $host = substr($hostPart, 0, $end + 1);
                $rest = substr($hostPart, $end + 1);
                if ($rest !== '') {
                    if ($rest[0] !== ':') {
                        throw new InvalidArgumentException('unexpected text after the IPv6 literal');
                    }
                    $port = self::parsePort(substr($rest, 1));
                }
            } else {
                $colon = strrpos($hostPart, ':');
                if ($colon === false) {
                    $host = $hostPart === '' ? null : strtolower($hostPart);
                } else {
                    $host = strtolower(substr($hostPart, 0, $colon));
                    $port = self::parsePort(substr($hostPart, $colon + 1));
                }
            }
        }

        $query = $match[4] ?? null;

        return [
            'scheme' => $scheme,
            'user' => $user,
            'password' => $password,
            'host' => $host,
            'port' => $port,
            'path' => $match[3] ?? '',
            'query' => ($query === null || $query === '') ? null : $query,
            'fragment' => $match[5] ?? null,
        ];
    }

    private static function parsePort(string $text): int
    {
        if ($text === '' || preg_match('/^\d{1,5}$/', $text) !== 1) {
            throw new InvalidArgumentException('port must be 1-5 digits');
        }

        $port = (int) $text;
        if ($port < 1 || $port > 65535) {
            throw new InvalidArgumentException('port must be between 1 and 65535');
        }

        return $port;
    }

    /**
     * @param array{scheme: ?string, user: ?string, password: ?string, host: ?string, port: ?int, path: string, query: ?string, fragment: ?string} $parts
     */
    public static function toString(array $parts): string
    {
        $uri = '';
        if ($parts['scheme'] !== null) {
            $uri .= $parts['scheme'] . ':';
        }
        if ($parts['host'] !== null) {
            $uri .= '//';
            if ($parts['user'] !== null) {
                $uri .= rawurlencode($parts['user']);
                if ($parts['password'] !== null) {
                    $uri .= ':' . rawurlencode($parts['password']);
                }
                $uri .= '@';
            }
            $uri .= $parts['host'];
            if ($parts['port'] !== null) {
                $uri .= ':' . $parts['port'];
            }
        }
        $uri .= self::removeDotSegments($parts['path']);
        if ($parts['query'] !== null) {
            $uri .= '?' . $parts['query'];
        }
        if ($parts['fragment'] !== null) {
            $uri .= '#' . $parts['fragment'];
        }

        return $uri;
    }

    /** Lowercases the scheme and host, drops the default port, resolves dot segments. */
    public static function normalize(string $uri): string
    {
        $parts = self::parse($uri);
        $scheme = $parts['scheme'];
        if ($scheme !== null && $parts['port'] !== null
            && (self::DEFAULT_PORTS[$scheme] ?? null) === $parts['port']) {
            $parts['port'] = null;
        }
        if ($parts['host'] !== null && $parts['path'] === '') {
            $parts['path'] = '/';
        }

        return self::toString($parts);
    }

    /** RFC 3986 section 5.2.4. */
    public static function removeDotSegments(string $path): string
    {
        if ($path === '') {
            return '';
        }

        $input = $path;
        $output = '';
        while ($input !== '') {
            if (str_starts_with($input, '../')) {
                $input = substr($input, 3);
            } elseif (str_starts_with($input, './')) {
                $input = substr($input, 2);
            } elseif (str_starts_with($input, '/./')) {
                $input = '/' . substr($input, 3);
            } elseif ($input === '/.') {
                $input = '/';
            } elseif (str_starts_with($input, '/../')) {
                $input = '/' . substr($input, 4);
                $output = preg_replace('~/[^/]*$~', '', $output) ?? '';
            } elseif ($input === '/..') {
                $input = '/';
                $output = preg_replace('~/[^/]*$~', '', $output) ?? '';
            } elseif ($input === '.' || $input === '..') {
                $input = '';
            } else {
                $next = strpos($input, '/', $input[0] === '/' ? 1 : 0);
                if ($next === false) {
                    $output .= $input;
                    $input = '';
                } else {
                    $output .= substr($input, 0, $next);
                    $input = substr($input, $next);
                }
            }
        }

        return $output;
    }

    /**
     * Query parameters in order, as key => value. A bare key (`?flag`) becomes
     * an empty string rather than being dropped.
     *
     * @return list<array{0: string, 1: string}>
     */
    public static function queryPairs(string $query): array
    {
        $pairs = [];
        foreach (explode('&', $query) as $chunk) {
            if ($chunk === '') {
                continue;
            }
            $parts = explode('=', $chunk, 2);
            $pairs[] = [rawurldecode($parts[0]), rawurldecode($parts[1] ?? '')];
        }

        return $pairs;
    }

    /**
     * Replaces the named parameters, keeping the order of everything else.
     *
     * @param list<array{0: string, 1: string}> $pairs
     * @param array<string, string> $replacements
     * @return list<array{0: string, 1: string}>
     */
    public static function mergeQuery(array $pairs, array $replacements): array
    {
        $merged = [];
        $seen = [];
        foreach ($pairs as [$key, $value]) {
            if (array_key_exists($key, $replacements)) {
                if (isset($seen[$key])) {
                    continue; // a replaced parameter keeps one copy only
                }
                $seen[$key] = true;
                $merged[] = [$key, $replacements[$key]];
                continue;
            }
            $merged[] = [$key, $value];
        }
        foreach ($replacements as $key => $value) {
            if (!isset($seen[$key]) && !self::hasKey($pairs, (string) $key)) {
                $merged[] = [(string) $key, $value];
            }
        }

        return $merged;
    }

    /** @param list<array{0: string, 1: string}> $pairs */
    private static function hasKey(array $pairs, string $key): bool
    {
        foreach ($pairs as [$candidate]) {
            if ($candidate === $key) {
                return true;
            }
        }

        return false;
    }

    /** @param list<array{0: string, 1: string}> $pairs */
    public static function encodeQuery(array $pairs): string
    {
        $chunks = [];
        foreach ($pairs as [$key, $value]) {
            $chunks[] = rawurlencode($key) . '=' . rawurlencode($value);
        }

        return implode('&', $chunks);
    }
}

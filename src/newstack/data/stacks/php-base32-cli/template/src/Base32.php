<?php

declare(strict_types=1);

namespace {{ package_name }};

use InvalidArgumentException;

/**
 * RFC 4648 base32, plus the Crockford variant used for identifiers.
 */
final class Base32
{
    public const ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';
    public const CROCKFORD = '0123456789ABCDEFGHJKMNPQRSTVWXYZ';

    public static function encode(string $bytes, bool $pad = true): string
    {
        return self::encodeWith(self::ALPHABET, $bytes, $pad);
    }

    public static function decode(string $text): string
    {
        return self::decodeWith(self::ALPHABET, $text);
    }

    public static function encodeCrockford(string $bytes): string
    {
        return rtrim(self::encodeWith(self::CROCKFORD, $bytes, true), '=');
    }

    public static function decodeCrockford(string $text): string
    {
        // Crockford treats i/l as 1 and o as 0, and ignores hyphens.
        $normalised = strtoupper(str_replace('-', '', $text));
        $normalised = strtr($normalised, ['I' => '1', 'L' => '1', 'O' => '0']);

        return self::decodeWith(self::CROCKFORD, $normalised);
    }

    private static function encodeWith(string $alphabet, string $bytes, bool $pad): string
    {
        $out = '';
        $buffer = 0;
        $bits = 0;
        $length = strlen($bytes);
        for ($index = 0; $index < $length; $index++) {
            $buffer = ($buffer << 8) | ord($bytes[$index]);
            $bits += 8;
            while ($bits >= 5) {
                $bits -= 5;
                $out .= $alphabet[($buffer >> $bits) & 0x1F];
            }
        }
        if ($bits > 0) {
            $out .= $alphabet[($buffer << (5 - $bits)) & 0x1F];
        }
        if ($pad) {
            while (strlen($out) % 8 !== 0) {
                $out .= '=';
            }
        }

        return $out;
    }

    private static function decodeWith(string $alphabet, string $text): string
    {
        $clean = strtoupper(preg_replace('/\s+/', '', $text) ?? '');
        $clean = rtrim($clean, '=');
        $out = '';
        $buffer = 0;
        $bits = 0;
        $length = strlen($clean);
        for ($index = 0; $index < $length; $index++) {
            $position = strpos($alphabet, $clean[$index]);
            if ($position === false) {
                throw new InvalidArgumentException(sprintf('invalid base32 character: %s', $clean[$index]));
            }
            $buffer = ($buffer << 5) | $position;
            $bits += 5;
            if ($bits >= 8) {
                $bits -= 8;
                $out .= chr(($buffer >> $bits) & 0xFF);
            }
        }

        return $out;
    }
}

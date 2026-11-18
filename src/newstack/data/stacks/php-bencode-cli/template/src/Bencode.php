<?php

declare(strict_types=1);

namespace {{ package_name }};

use InvalidArgumentException;

/**
 * Bencode — the encoding BitTorrent uses for torrent files and tracker
 * responses. Four types, no floats, no nulls:
 *
 *   integer   i42e          (also negative: i-7e)
 *   string    4:spam        (byte length, then the bytes)
 *   list      l4:spami1ee  (values until 'e')
 *   dict      d3:bar4:spame (key/value pairs, keys sorted, until 'e')
 *
 * Decoding enforces canonical form: integer literals cannot carry leading
 * zeroes, and dictionary keys must be strictly ascending, so two encoders that
 * agree on the value also agree on the bytes. That is what makes a bencoded
 * file hashable.
 */
final class Bencode
{
    public static function encode(mixed $value): string
    {
        return self::encodeValue($value);
    }

    /**
     * @throws InvalidArgumentException when the text is not canonical bencode
     */
    public static function decode(string $text): mixed
    {
        $offset = 0;
        $value = self::decodeValue($text, $offset);

        if ($offset !== strlen($text)) {
            throw new InvalidArgumentException("trailing data at offset {$offset}");
        }

        return $value;
    }

    private static function encodeValue(mixed $value): string
    {
        if (is_bool($value)) {
            $value = $value ? 1 : 0;
        }

        if (is_int($value)) {
            return 'i' . $value . 'e';
        }

        if (is_float($value)) {
            throw new InvalidArgumentException('bencode has no float type; pass an int or a string');
        }

        if (is_string($value)) {
            return strlen($value) . ':' . $value;
        }

        if (is_array($value)) {
            if (array_is_list($value)) {
                $out = 'l';
                foreach ($value as $item) {
                    $out .= self::encodeValue($item);
                }

                return $out . 'e';
            }

            $keys = array_keys($value);
            foreach ($keys as $key) {
                if (!is_string($key)) {
                    throw new InvalidArgumentException('dictionary keys must be strings');
                }
            }
            sort($keys, SORT_STRING);

            $out = 'd';
            foreach ($keys as $key) {
                $out .= self::encodeValue($key) . self::encodeValue($value[$key]);
            }

            return $out . 'e';
        }

        throw new InvalidArgumentException('cannot encode a value of type ' . get_debug_type($value));
    }

    private static function decodeValue(string $text, int &$offset): mixed
    {
        if ($offset >= strlen($text)) {
            throw new InvalidArgumentException("unexpected end of input at offset {$offset}");
        }

        $marker = $text[$offset];

        if ($marker === 'i') {
            return self::decodeInteger($text, $offset);
        }

        if ($marker === 'l') {
            $offset++;
            $items = [];
            while (true) {
                if ($offset >= strlen($text)) {
                    throw new InvalidArgumentException('unterminated list');
                }
                if ($text[$offset] === 'e') {
                    $offset++;

                    return $items;
                }
                $items[] = self::decodeValue($text, $offset);
            }
        }

        if ($marker === 'd') {
            $offset++;
            $entries = [];
            $previous = null;
            while (true) {
                if ($offset >= strlen($text)) {
                    throw new InvalidArgumentException('unterminated dictionary');
                }
                if ($text[$offset] === 'e') {
                    $offset++;

                    return $entries;
                }
                if (!ctype_digit($text[$offset])) {
                    throw new InvalidArgumentException("dictionary key at offset {$offset} is not a string");
                }
                $key = self::decodeString($text, $offset);
                if ($previous !== null && strcmp($key, $previous) <= 0) {
                    throw new InvalidArgumentException("dictionary keys are not in canonical order at offset {$offset}");
                }
                if (array_key_exists($key, $entries)) {
                    throw new InvalidArgumentException("duplicate dictionary key '{$key}'");
                }
                $previous = $key;
                $entries[$key] = self::decodeValue($text, $offset);
            }
        }

        if (ctype_digit($marker)) {
            return self::decodeString($text, $offset);
        }

        throw new InvalidArgumentException("unknown type marker '{$marker}' at offset {$offset}");
    }

    private static function decodeInteger(string $text, int &$offset): int
    {
        $end = strpos($text, 'e', $offset);
        if ($end === false) {
            throw new InvalidArgumentException('unterminated integer');
        }

        $literal = substr($text, $offset + 1, $end - $offset - 1);
        if (preg_match('/^(0|-?[1-9][0-9]*)$/', $literal) !== 1) {
            throw new InvalidArgumentException("malformed integer '{$literal}' at offset {$offset}");
        }

        $offset = $end + 1;

        return (int) $literal;
    }

    private static function decodeString(string $text, int &$offset): string
    {
        $colon = strpos($text, ':', $offset);
        if ($colon === false) {
            throw new InvalidArgumentException("string length at offset {$offset} has no ':'");
        }

        $literal = substr($text, $offset, $colon - $offset);
        if (preg_match('/^(0|[1-9][0-9]*)$/', $literal) !== 1) {
            throw new InvalidArgumentException("malformed string length '{$literal}' at offset {$offset}");
        }

        $length = (int) $literal;
        $start = $colon + 1;
        if ($start + $length > strlen($text)) {
            throw new InvalidArgumentException("string of length {$length} at offset {$offset} runs past the end");
        }

        $offset = $start + $length;

        return substr($text, $start, $length);
    }
}

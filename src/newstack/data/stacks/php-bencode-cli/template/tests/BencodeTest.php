<?php

declare(strict_types=1);

namespace {{ package_name }}\Tests;

use InvalidArgumentException;
use PHPUnit\Framework\Attributes\DataProvider;
use PHPUnit\Framework\TestCase;
use {{ package_name }}\Bencode;

final class BencodeTest extends TestCase
{
    /** @return array<string, array{0: mixed, 1: string}> */
    public static function encodings(): array
    {
        return [
            'zero' => [0, 'i0e'],
            'negative' => [-7, 'i-7e'],
            'empty string' => ['', '0:'],
            'short string' => ['spam', '4:spam'],
            'empty list' => [[], 'le'],
            'list of mixed' => [["spam", 42], 'l4:spami42ee'],
            'nested list' => [[[1, 2], []], 'lli1ei2eelee'],
            'dict sorts keys' => [['b' => 2, 'a' => 1], 'd1:ai1e1:bi2ee'],
            'nested dict' => [['a' => ['b' => 'c']], 'd1:ad1:b1:cee'],
            'bool becomes int' => [true, 'i1e'],
            'multibyte string uses bytes' => ['é', '2:' . 'é'],
        ];
    }

    #[DataProvider('encodings')]
    public function test_it_encodes(mixed $value, string $expected): void
    {
        self::assertSame($expected, Bencode::encode($value));
    }

    public function test_it_round_trips_nested_structures(): void
    {
        $value = ['name' => 'ubuntu-24.04.iso', 'pieces' => ['abc', 'def'], 'length' => 4096,
            'meta' => ['private' => 1]];
        // Dictionaries come back with sorted keys, so compare by value, not order.
        self::assertEquals($value, Bencode::decode(Bencode::encode($value)));
    }

    public function test_it_rejects_floats(): void
    {
        $this->expectException(InvalidArgumentException::class);
        $this->expectExceptionMessage('no float type');
        Bencode::encode(1.5);
    }

    public function test_it_rejects_leading_zeroes(): void
    {
        $this->expectException(InvalidArgumentException::class);
        Bencode::decode('i03e');
    }

    public function test_it_rejects_negative_zero(): void
    {
        $this->expectException(InvalidArgumentException::class);
        Bencode::decode('i-0e');
    }

    public function test_it_rejects_unsorted_dictionary_keys(): void
    {
        $this->expectException(InvalidArgumentException::class);
        $this->expectExceptionMessage('canonical order');
        Bencode::decode('d1:bi2e1:ai1ee');
    }

    public function test_it_rejects_duplicate_keys(): void
    {
        $this->expectException(InvalidArgumentException::class);
        Bencode::decode('d1:ai1e1:ai2ee');
    }

    public function test_it_rejects_trailing_data(): void
    {
        $this->expectException(InvalidArgumentException::class);
        $this->expectExceptionMessage('trailing data');
        Bencode::decode('i1ei2e');
    }

    public function test_it_rejects_a_truncated_string(): void
    {
        $this->expectException(InvalidArgumentException::class);
        $this->expectExceptionMessage('runs past the end');
        Bencode::decode('5:abc');
    }

    public function test_it_rejects_an_unterminated_list(): void
    {
        $this->expectException(InvalidArgumentException::class);
        $this->expectExceptionMessage('unterminated list');
        Bencode::decode('li1e');
    }

    public function test_it_rejects_an_unknown_marker(): void
    {
        $this->expectException(InvalidArgumentException::class);
        $this->expectExceptionMessage('unknown type marker');
        Bencode::decode('x1e');
    }

    public function test_binary_strings_survive(): void
    {
        $bytes = "\x00\x01\xff";
        self::assertSame($bytes, Bencode::decode(Bencode::encode($bytes)));
    }
}

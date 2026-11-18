<?php

declare(strict_types=1);

namespace {{ package_name }}\Tests;

use {{ package_name }}\Base32;
use PHPUnit\Framework\Attributes\DataProvider;
use InvalidArgumentException;
use PHPUnit\Framework\TestCase;

final class Base32Test extends TestCase
{
    /**
     * The RFC 4648 section 10 test vectors, verbatim.
     *
     * @return array<string, array{string, string}>
     */
    public static function vectors(): array
    {
        return [
            'empty' => ['', ''],
            'f' => ['f', 'MY======'],
            'fo' => ['fo', 'MZXQ===='],
            'foo' => ['foo', 'MZXW6==='],
            'foob' => ['foob', 'MZXW6YQ='],
            'fooba' => ['fooba', 'MZXW6YTB'],
            'foobar' => ['foobar', 'MZXW6YTBOI======'],
        ];
    }

    #[DataProvider('vectors')]
    public function testEncodeMatchesRfc4648(string $plain, string $encoded): void
    {
        self::assertSame($encoded, Base32::encode($plain));
    }

    #[DataProvider('vectors')]
    public function testDecodeMatchesRfc4648(string $plain, string $encoded): void
    {
        self::assertSame($plain, Base32::decode($encoded));
    }

    public function testUnpaddedEncodingDropsEqualsSigns(): void
    {
        self::assertSame('MZXW6YTBOI', Base32::encode('foobar', false));
    }

    public function testDecodingIgnoresPaddingWhitespaceAndCase(): void
    {
        self::assertSame('foobar', Base32::decode("mzxw6ytboi======\n"));
        self::assertSame('foobar', Base32::decode('MZXW 6YTB OI'));
    }

    public function testInvalidCharacterIsRejected(): void
    {
        $this->expectException(InvalidArgumentException::class);
        $this->expectExceptionMessage('invalid base32 character: 1');
        Base32::decode('MZXW1YTB');
    }

    public function testRandomBytesSurviveARoundTrip(): void
    {
        $bytes = random_bytes(37);
        self::assertSame($bytes, Base32::decode(Base32::encode($bytes)));
    }

    public function testCrockfordAlphabetEncodesKnownValue(): void
    {
        // 0x00 0x01 0x02 is five 5-bit groups: 00000 00000 00000 10000 00100
        self::assertSame('000G4', Base32::encodeCrockford("\x00\x01\x02"));
        self::assertSame("\x00\x01\x02", Base32::decodeCrockford('000g4'));
    }

    public function testCrockfordNormalisesLookalikes(): void
    {
        self::assertSame(Base32::decodeCrockford('000G4'), Base32::decodeCrockford('OOOG4'));
    }
}

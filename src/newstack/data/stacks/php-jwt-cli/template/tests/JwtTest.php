<?php
declare(strict_types=1);

namespace {{ package_name }}\Tests;

use PHPUnit\Framework\TestCase;
use {{ package_name }}\Jwt;
use {{ package_name }}\FixedClock;

final class JwtTest extends TestCase
{
    public function testBase64UrlRoundTrip(): void
    {
        $data = "hello\x00world/+";
        $enc = Jwt::base64UrlEncode($data);
        $this->assertStringNotContainsString('=', $enc);
        $this->assertStringNotContainsString('+', $enc);
        $this->assertStringNotContainsString('/', $enc);
        $this->assertSame($data, Jwt::base64UrlDecode($enc));
    }

    public function testSignVerify(): void
    {
        $clock = new FixedClock(1000);
        $token = Jwt::sign(['sub' => 'alice', 'exp' => 2000], 'secret', $clock);
        $payload = Jwt::verify($token, 'secret', $clock);
        $this->assertIsArray($payload);
        $this->assertSame('alice', $payload['sub']);
        $this->assertSame(1000, $payload['iat']);
    }

    public function testExpired(): void
    {
        $clock = new FixedClock(1000);
        $token = Jwt::sign(['sub' => 'alice', 'exp' => 1500], 'secret', $clock);
        $later = new FixedClock(1500);
        $this->assertNull(Jwt::verify($token, 'secret', $later));
        $earlier = new FixedClock(1499);
        $this->assertNotNull(Jwt::verify($token, 'secret', $earlier));
    }

    public function testTampered(): void
    {
        $clock = new FixedClock(1000);
        $token = Jwt::sign(['sub' => 'alice', 'exp' => 2000], 'secret', $clock);
        $parts = explode('.', $token);
        $parts[1] = Jwt::base64UrlEncode(json_encode(['sub' => 'bob', 'exp' => 2000]));
        $bad = implode('.', $parts);
        $this->assertNull(Jwt::verify($bad, 'secret', $clock));
        $this->assertNull(Jwt::verify($token, 'wrong', $clock));
    }

    public function testMalformed(): void
    {
        $this->assertNull(Jwt::verify('a.b', 'secret'));
        $this->assertNull(Jwt::verify('a.b.c.d', 'secret'));
    }
}

<?php
declare(strict_types=1);

// php-jwt-cli

namespace {{ package_name }};

final class Jwt
{
    public static function base64UrlEncode(string $data): string
    {
        return rtrim(strtr(base64_encode($data), '+/', '-_'), '=');
    }

    public static function base64UrlDecode(string $data): string
    {
        $pad = (4 - (strlen($data) % 4)) % 4;
        if ($pad > 0) {
            $data .= str_repeat('=', $pad);
        }
        $decoded = base64_decode(strtr($data, '-_', '+/'), true);
        return $decoded === false ? '' : $decoded;
    }

    public static function sign(array $claims, string $secret, ?Clock $clock = null): string
    {
        $header = ['typ' => 'JWT', 'alg' => 'HS256'];
        $payload = $claims;
        if ($clock !== null && !array_key_exists('iat', $payload)) {
            $payload['iat'] = $clock->now();
        }
        $h = self::base64UrlEncode((string) json_encode($header, JSON_UNESCAPED_SLASHES));
        $p = self::base64UrlEncode((string) json_encode($payload, JSON_UNESCAPED_SLASHES));
        $sig = hash_hmac('sha256', $h . '.' . $p, $secret, true);
        return $h . '.' . $p . '.' . self::base64UrlEncode($sig);
    }

    public static function verify(string $token, string $secret, ?Clock $clock = null): ?array
    {
        $parts = explode('.', $token);
        if (count($parts) !== 3) {
            return null;
        }
        [$h, $p, $s] = $parts;
        $calc = self::base64UrlEncode(hash_hmac('sha256', $h . '.' . $p, $secret, true));
        if (!hash_equals($calc, $s)) {
            return null;
        }
        $decoded = self::base64UrlDecode($p);
        $payload = json_decode($decoded, true);
        if (!is_array($payload)) {
            return null;
        }
        $now = $clock !== null ? $clock->now() : time();
        if (isset($payload['exp']) && $now >= (int) $payload['exp']) {
            return null;
        }
        if (isset($payload['nbf']) && $now < (int) $payload['nbf']) {
            return null;
        }
        return $payload;
    }
}

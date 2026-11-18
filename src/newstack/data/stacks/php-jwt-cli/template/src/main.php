<?php
declare(strict_types=1);

require __DIR__ . '/../vendor/autoload.php';

use {{ package_name }}\Jwt;
use {{ package_name }}\SystemClock;

$args = array_slice($argv, 1);
$cmd = $args[0] ?? '';
array_shift($args);

if ($cmd === 'sign') {
    $secret = $args[0] ?? '';
    $json = $args[1] ?? '{}';
    $claims = json_decode($json, true);
    if (!is_array($claims)) {
        fwrite(STDERR, "invalid claims json\n");
        exit(2);
    }
    echo Jwt::sign($claims, $secret, new SystemClock()) . "\n";
    exit(0);
}

if ($cmd === 'verify') {
    $secret = $args[0] ?? '';
    $token = $args[1] ?? '';
    $payload = Jwt::verify($token, $secret, new SystemClock());
    if ($payload === null) {
        fwrite(STDERR, "invalid\n");
        exit(1);
    }
    echo json_encode($payload, JSON_UNESCAPED_SLASHES) . "\n";
    exit(0);
}

fwrite(STDERR, "usage: php main.php sign|verify ...\n");
exit(2);

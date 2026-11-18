<?php
declare(strict_types=1);

require __DIR__ . '/../vendor/autoload.php';

use {{ package_name }}\Sanitizer;

$input = $argv[1] ?? null;
if ($input === null && !stream_isatty(STDIN)) {
    $input = stream_get_contents(STDIN);
}
if ($input === null) {
    fwrite(STDERR, "usage: php src/main.php '<p>html</p>'\n");
    exit(2);
}

$sanitizer = new Sanitizer();
echo $sanitizer->sanitize($input) . "\n";

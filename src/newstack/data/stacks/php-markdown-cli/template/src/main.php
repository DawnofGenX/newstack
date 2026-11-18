<?php
declare(strict_types=1);

require __DIR__ . '/../vendor/autoload.php';

use {{ package_name }}\Markdown;

$args = array_slice($argv, 1);
$input = '';
if (isset($args[0]) && $args[0] !== '' && $args[0] !== '-') {
    $input = (string) file_get_contents($args[0]);
} else {
    $input = (string) stream_get_contents(STDIN);
}
echo Markdown::toHtml($input);

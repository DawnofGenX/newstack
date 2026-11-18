<?php
declare(strict_types=1);

require __DIR__ . '/../vendor/autoload.php';

use {{ package_name }}\Csv;
use {{ package_name }}\Report;

$args = array_slice($argv, 1);
$path = $args[0] ?? '-';
array_shift($args);

$text = $path === '-' ? stream_get_contents(STDIN) : file_get_contents($path);
if ($text === false) {
    fwrite(STDERR, "cannot read input\n");
    exit(2);
}
$table = Csv::parse($text);

$groupCol = null;
$sumCol = null;
foreach ($args as $a) {
    if (str_starts_with($a, '--group=')) {
        $groupCol = substr($a, 8);
    } elseif (str_starts_with($a, '--sum=')) {
        $sumCol = substr($a, 6);
    }
}
$groupCol = $groupCol ?? ($table['headers'][0] ?? '');

echo "rows=" . count($table['rows']) . "\n";
$counts = Report::groupCount($table, $groupCol);
foreach ($counts as $k => $v) {
    echo $k . " " . $v . "\n";
}
if ($sumCol !== null) {
    echo "sum=" . Report::sum($table, $sumCol) . "\n";
}
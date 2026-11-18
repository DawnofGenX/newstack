<?php

declare(strict_types=1);

require __DIR__ . '/../vendor/autoload.php';

$app = {{ package_name }}\Api::createApp();
$app->run();

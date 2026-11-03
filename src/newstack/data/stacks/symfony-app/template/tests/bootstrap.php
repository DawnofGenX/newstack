<?php

declare(strict_types=1);

use Symfony\Component\Dotenv\Dotenv;

require dirname(__DIR__).'/vendor/autoload.php';

// Load the app's .env (APP_SECRET, DEFAULT_URI, ...). Values PHPUnit already
// set (APP_ENV=test, APP_DEBUG=1) win over .env because bootEnv does not
// override existing variables by default.
(new Dotenv())->bootEnv(dirname(__DIR__).'/.env');

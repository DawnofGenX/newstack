<?php

declare(strict_types=1);

namespace {{ package_name }};

use RuntimeException;

/** Raised for an input problem that is not a template syntax error. */
final class CliException extends RuntimeException
{
}

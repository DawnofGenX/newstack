<?php

declare(strict_types=1);

namespace {{ package_name }};

use RuntimeException;

/** Raised when a template cannot be parsed. */
final class MustacheException extends RuntimeException
{
}

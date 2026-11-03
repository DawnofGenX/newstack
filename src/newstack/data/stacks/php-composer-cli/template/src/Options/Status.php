<?php

declare(strict_types=1);

namespace {{ package_name }}\Options;

/** How argument parsing ended. */
enum Status
{
    case OK;
    case HELP;
    case VERSION;
    case ERROR;
}

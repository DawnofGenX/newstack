<?php

declare(strict_types=1);

namespace {{ package_name }}\Options;

/** Which figures to print; ALL prints lines, words and bytes. */
enum Mode
{
    case ALL;
    case LINES;
    case WORDS;
    case BYTES;
}

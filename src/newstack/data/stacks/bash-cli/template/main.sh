#!/usr/bin/env bash
# The entry point: the only place that knows about real files, real standard
# input, and the process exit status.
set -uo pipefail

# Byte semantics everywhere: ${#data} must count bytes, not characters.
export LC_ALL=C

here=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)

# shellcheck source=lib/counts.sh
. "$here/lib/counts.sh"
# shellcheck source=lib/options.sh
. "$here/lib/options.sh"
# shellcheck source=lib/io.sh
. "$here/lib/io.sh"
# shellcheck source=lib/runner.sh
. "$here/lib/runner.sh"

textstat_runner_run '{{ npm_name }}' "$@"
status=$?
exit "$status"

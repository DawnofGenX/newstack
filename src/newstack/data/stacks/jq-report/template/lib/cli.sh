#!/usr/bin/env bash
# jq-report: small, readable reports over a JSON access log.
#
# The filters live in filters/*.jq and are plain jq programs: no wrapper magic,
# so "jq -f filters/top-paths.jq data/sample.json" gives the same answer as
# "run top-paths data/sample.json". This file only parses arguments, finds the
# filter, and turns jq's exit status into one this tool promises to keep.
set -u

readonly PROG="${JQREPORT_PROG:-jq-report}"
ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
readonly ROOT
readonly FILTERS="$ROOT/filters"

usage() {
  cat <<EOF
Usage: $PROG COMMAND [ARG]...

Read a JSON access log (an array of objects) and print a report.

Commands:
  run FILTER [FILE]   apply filters/FILTER.jq to FILE (default: standard input)
  filters             list the available filters, one per line
  lint [DIR]          check that every filter in DIR (default: filters/) compiles
  help                show this message

Examples:
  $PROG filters
  $PROG run status-counts data/sample.json
  $PROG run error-rate < data/sample.json
  $PROG lint

Exit status:
  0  success
  1  the input could not be read, or is not valid JSON
  2  usage error
EOF
}

die_usage() {
  printf '%s: %s\n' "$PROG" "$1" >&2
  printf "Try '%s help' for more information.\n" "$PROG" >&2
  exit 2
}

die_data() {
  printf '%s: %s\n' "$PROG" "$1" >&2
  exit 1
}

list_filters() {
  local file
  shopt -s nullglob
  for file in "$FILTERS"/*.jq; do
    printf '%s\n' "${file##*/}" | sed 's/\.jq$//'
  done
}

cmd_run() {
  if [ "$#" -lt 1 ]; then
    die_usage "run needs a filter name"
  fi
  if [ "$#" -gt 2 ]; then
    die_usage "run takes at most two arguments"
  fi
  local name="$1"
  local file="${2:--}"
  local filter="$FILTERS/$name.jq"

  if [ ! -f "$filter" ]; then
    die_usage "no such filter: $name"
  fi
  if [ "$file" != "-" ] && [ ! -r "$file" ]; then
    die_data "cannot read $file"
  fi

  local out err status
  out=$(mktemp) || die_data "cannot create a temporary file"
  err=$(mktemp) || die_data "cannot create a temporary file"
  # shellcheck disable=SC2064
  trap "rm -f '$out' '$err'" EXIT

  jq -c -f "$filter" -- "$file" >"$out" 2>"$err"
  status=$?
  if [ "$status" -eq 0 ]; then
    cat "$out"
    return 0
  fi
  local message
  message=$(head -n 1 "$err" | sed 's/^jq: //')
  case $message in
    *"parse error"* | *"Invalid numeric literal"*) die_data "$file is not valid JSON" ;;
    *) die_data "${message:-jq failed on $file}" ;;
  esac
}

cmd_lint() {
  local dir="${1:-$FILTERS}"
  if [ ! -d "$dir" ]; then
    die_usage "no such directory: $dir"
  fi
  local bad=0 file status
  shopt -s nullglob
  for file in "$dir"/*.jq; do
    # jq exits 3 only when the program does not compile; runtime errors on the
    # null input (exit 5) are fine, the filter is still well formed.
    jq -n -f "$file" >/dev/null 2>&1
    status=$?
    if [ "$status" -eq 3 ]; then
      printf '%s: %s does not compile\n' "$PROG" "${file##*/}" >&2
      bad=1
    else
      printf 'ok   %s\n' "${file##*/}"
    fi
  done
  if [ "$bad" -ne 0 ]; then
    exit 1
  fi
}

main() {
  local command="${1:-}"
  case $command in
    help | -h | --help)
      usage
      exit 0
      ;;
    filters)
      shift
      if [ "$#" -gt 0 ]; then die_usage "filters takes no arguments"; fi
      list_filters
      ;;
    lint)
      shift
      if [ "$#" -gt 1 ]; then die_usage "lint takes at most one directory"; fi
      cmd_lint "$@"
      ;;
    run)
      shift
      cmd_run "$@"
      ;;
    "")
      die_usage "no command given"
      ;;
    -*)
      die_usage "unknown option: $command"
      ;;
    *)
      die_usage "unknown command: $command"
      ;;
  esac
}

main "$@"

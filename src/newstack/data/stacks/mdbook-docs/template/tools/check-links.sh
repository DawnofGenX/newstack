#!/usr/bin/env bash
# Check that a book is intact: every relative link resolves, and every page is
# reachable from the summary.
#
#   tools/check-links.sh [ROOT]
#
# ROOT defaults to the project this script lives in. Exit status: 0 intact,
# 1 something is broken, 2 usage error.
set -u

PROG=${0##*/}

usage() {
  cat <<EOF
Usage: $PROG [ROOT]

Check every markdown file under ROOT/src: relative links and images must point
at files that exist, and every page must be listed in ROOT/src/SUMMARY.md.

ROOT defaults to the project containing this script.

Exit status:
  0  the book is intact
  1  at least one link is broken or one page is not in the summary
  2  usage error
EOF
}

if [ "$#" -gt 1 ]; then
  printf '%s: too many arguments\n' "$PROG" >&2
  exit 2
fi
case ${1:-} in
  -h | --help)
    usage
    exit 0
    ;;
esac

if [ -n "${1:-}" ]; then
  if [ ! -d "$1" ]; then
    printf '%s: no such directory: %s\n' "$PROG" "$1" >&2
    exit 2
  fi
  ROOT=$(cd -- "$1" && pwd)
else
  ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
fi

SRC="$ROOT/src"
if [ ! -d "$SRC" ]; then
  printf '%s: %s has no src/ directory\n' "$PROG" "$ROOT" >&2
  exit 2
fi

# A link is a URL only if it carries a scheme; everything else is a path in
# this repository. We deliberately do not resolve reference-style links
# ("[text]: target"): the book does not use them, and guessing would be worse
# than saying so in the README.
is_external() {
  case $1 in
    //* | *://* | mailto:* | tel:* | data:*) return 0 ;;
  esac
  return 1
}

problems=0
files=0
links=0

report() { # file line message
  if [ -n "$2" ]; then
    printf '%s:%s: %s\n' "$1" "$2" "$3"
  else
    printf '%s: %s\n' "$1" "$3"
  fi
  problems=$((problems + 1))
}

cd "$SRC" || exit 2
while IFS= read -r file; do
  files=$((files + 1))
  dir=$(dirname "$file")
  # "grep -n" gives the line number of the match, so a problem names a line.
  while IFS= read -r match; do
    [ -n "$match" ] || continue
    line=${match%%:*}
    raw=${match#*:}
    target=${raw#*](}
    target=${target%)}
    target=${target#<}
    target=${target%>}
    # Trim the spaces markdown allows around a destination.
    while [ "${target# }" != "$target" ]; do target=${target# }; done
    while [ "${target% }" != "$target" ]; do target=${target% }; done
    [ -n "$target" ] || continue
    is_external "$target" && continue
    case $target in
      \#*) continue ;;
    esac
    links=$((links + 1))
    path=${target%%#*}
    path=${path%%\?*}
    [ -n "$path" ] || continue
    case $path in
      /*) resolved="$ROOT$path" ;;
      *) resolved="$SRC/$dir/$path" ;;
    esac
    if [ ! -e "$resolved" ]; then
      report "src/${file#./}" "$line" "$target does not exist"
    fi
  done <<LINES
$(grep -noE '\]\([^()]*\)' "$file" 2>/dev/null || true)
LINES
done <<FILES
$(find . -type f -name '*.md' | sed 's|^\./||' | sort)
FILES

# Every page except the summary must be reachable from the summary.
if [ -f "SUMMARY.md" ]; then
  summary=$(grep -oE '\]\([^()]*\)' SUMMARY.md | sed 's/^](//; s/)$//; s/#.*$//; s|^\./||' | sort -u)
  for page in $(find . -type f -name '*.md' | sed 's|^\./||' | sort); do
    [ "$page" = "SUMMARY.md" ] && continue
    if ! printf '%s\n' "$summary" | grep -qxF "$page"; then
      report "src/$page" "" "not listed in src/SUMMARY.md"
    fi
  done
else
  report "src/SUMMARY.md" "" "missing"
fi

if [ "$problems" -eq 0 ]; then
  printf 'checked %d file(s), %d link(s): ok\n' "$files" "$links"
  exit 0
fi
printf 'checked %d file(s), %d link(s): %d problem(s)\n' "$files" "$links" "$problems"
exit 1

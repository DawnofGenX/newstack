#!/usr/bin/env bash
set -euo pipefail

echo "smoke: java-lru-cache"

mvn -B test
mvn -B package -DskipTests

JAR="target/{{ npm_name }}.jar"
test -f "$JAR"

out=$(printf 'PUT a 1\nPUT b 2\nGET a\nPUT c 3\nKEYS\nSTATS\n' | java -jar "$JAR" -c 2)
echo "$out"
echo "$out" | grep -q 'GET a -> 1 (hit)'
echo "$out" | grep -q 'PUT c size=2 evicted=b'
echo "$out" | grep -q 'KEYS c a'
echo "$out" | grep -q 'STATS hits=1 misses=0 evictions=1 size=2/2'

if printf 'FROB\n' | java -jar "$JAR" >/dev/null 2>&1; then
  echo "smoke: a bad command must exit 1" >&2
  exit 1
fi
if java -jar "$JAR" --bogus >/dev/null 2>&1; then
  echo "smoke: an unknown option must exit 2" >&2
  exit 1
fi

echo "smoke: PASS"

#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "smoke: java-template-engine"

mvn -B -q test
mvn -B -q package -DskipTests

JAR="target/{{ npm_name }}.jar"
test -f "$JAR"

tmp=$(mktemp)
printf 'Hello {{! name }}, count={{! n }}' > "$tmp"
out=$(java -jar "$JAR" "$tmp" name=World n=7)
echo "$out"
echo "$out" | grep -q "Hello World, count=7"
rm -f "$tmp"

echo "smoke: PASS"
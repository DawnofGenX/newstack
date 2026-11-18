#!/usr/bin/env bash
set -euo pipefail

echo "smoke: java-json-flatten"

mvn -B test
mvn -B package -DskipTests

JAR="target/{{ npm_name }}.jar"
test -f "$JAR"

tmp=$(mktemp)
printf '{"a":{"b":1,"c":"x"},"d":[10,20]}' > "$tmp"
out=$(java -jar "$JAR" "$tmp")
echo "$out"
echo "$out" | grep -q '"a.b":1'
echo "$out" | grep -q '"d.0":10'

rm -f "$tmp"
echo "smoke: PASS"

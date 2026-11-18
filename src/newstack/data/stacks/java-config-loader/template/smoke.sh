#!/usr/bin/env bash
set -euo pipefail

echo "smoke: java-config-loader"

mvn -B test
mvn -B package -DskipTests

JAR="target/{{ npm_name }}.jar"
test -f "$JAR"

tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT
printf 'db.host=localhost\ndb.port=5432\n' > "$tmp"

out=$(java -jar "$JAR" "$tmp" db.host)
echo "$out"
echo "$out" | grep -qx 'localhost'

out2=$(java -jar "$JAR" "$tmp" db.port 3306)
echo "$out2" | grep -qx '5432'

out3=$(java -jar "$JAR" "$tmp" missing.key defaultval)
echo "$out3" | grep -qx 'defaultval'

echo "smoke: PASS"

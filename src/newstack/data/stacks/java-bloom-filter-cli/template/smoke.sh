#!/bin/sh
set -eu
echo "smoke: {{ npm_name }}"
mvn -B test
mvn -B package -DskipTests
JAR="target/{{ npm_name }}.jar"
test -f "$JAR"
printf 'apple\nbanana\ncherry\n' | java -jar "$JAR" contains apple | grep -qx 'probably'
printf 'apple\nbanana\ncherry\n' | java -jar "$JAR" contains zzz | grep -qx 'no'
echo "smoke: PASS"

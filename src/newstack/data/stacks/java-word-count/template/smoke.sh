#!/usr/bin/env bash
set -euo pipefail

echo "smoke: java-word-count"

mvn -B test
mvn -B package -DskipTests

JAR="target/{{ npm_name }}.jar"
test -f "$JAR"

top=$(printf 'the cat sat on the mat the end' | java -jar "$JAR" --top 2)
echo "$top"
test "$top" = "$(printf 'the 3\ncat 1')"

word=$(printf 'the cat sat on the mat the end' | java -jar "$JAR" --word The)
test "$word" = "The 3"

all=$(printf 'one two two' | java -jar "$JAR" --all)
test "$all" = "$(printf 'two 2\none 1')"

set +e
java -jar "$JAR" --bogus < /dev/null > /dev/null 2>&1
code=$?
set -e
test "$code" -eq 2

echo "smoke: PASS"

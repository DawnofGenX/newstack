#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "smoke: java-http-client-api"

mvn -B -q test
mvn -B -q package -DskipTests

JAR="target/{{ npm_name }}.jar"
test -f "$JAR"

PORT=$(python3 -c 'import socket; s=socket.socket(); s.bind(("",0)); print(s.getsockname()[1]); s.close()')
TMP=$(mktemp -d)
printf 'hello\n' > "$TMP/index.html"
python3 -m http.server "$PORT" --directory "$TMP" >/dev/null 2>&1 &
SRV=$!
trap 'kill $SRV 2>/dev/null || true; rm -rf "$TMP"' EXIT
for i in $(seq 1 50); do
  if curl -s "http://127.0.0.1:$PORT/" >/dev/null 2>&1; then break; fi
  sleep 0.1
done

out=$(java -jar "$JAR" "http://127.0.0.1:$PORT/")
echo "$out"
echo "$out" | grep -q "200"
echo "$out" | grep -q "hello"

echo "smoke: PASS"
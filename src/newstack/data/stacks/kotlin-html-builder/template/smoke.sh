#!/usr/bin/env bash
set -euo pipefail

echo "smoke: {{ npm_name }}"

gradle test
gradle run

echo "smoke: PASS"

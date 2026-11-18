#!/usr/bin/env bash
set -euo pipefail

echo "smoke: kotlin-coroutines-pipeline"

gradle test
gradle run

echo "smoke: PASS"

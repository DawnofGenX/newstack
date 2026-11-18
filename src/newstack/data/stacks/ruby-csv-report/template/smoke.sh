#!/usr/bin/env bash
set -euo pipefail

echo "smoke: {{ npm_name }}"

rake test
printf 'dept,salary\neng,100\nhr,50\n' > /tmp/smoke.csv
bin/{{ npm_name }} /tmp/smoke.csv --group dept

echo "smoke: PASS"

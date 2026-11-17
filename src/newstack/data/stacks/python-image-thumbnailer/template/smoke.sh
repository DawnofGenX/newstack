#!/usr/bin/env bash
set -euo pipefail
.venv/bin/python -m pytest
tmp=$(mktemp -d)
.venv/bin/python -c "from PIL import Image; Image.new('RGB',(10,10)).save('$tmp/a.png')"
.venv/bin/python -m {{ package_name }} thumbnail "$tmp/a.png" "$tmp/out.jpg" --size 8x8
test -f "$tmp/out.jpg"
echo "smoke: PASS"
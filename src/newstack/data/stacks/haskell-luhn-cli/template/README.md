# {{ project_name }}

Luhn check-digit validation and generation.

## Usage

```
./bin/{{ npm_name }} validate 79927398713
# valid (exit 0)

./bin/{{ npm_name }} validate 79927398710
# invalid (exit 1)

./bin/{{ npm_name }} generate 7992739871
# 79927398713
```

Exit codes: 0 valid/success, 1 invalid, 2 usage.
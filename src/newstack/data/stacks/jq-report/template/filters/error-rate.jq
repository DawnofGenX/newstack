# One object: how many requests failed with 5xx, and what share that is.
{total: length, errors: (map(select(.status >= 500)) | length)}
| . + {error_rate: (if .total == 0 then 0 else ((.errors / .total * 1000) | round) / 10 end)}

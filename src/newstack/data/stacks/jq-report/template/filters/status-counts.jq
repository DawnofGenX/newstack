# How many requests landed on each status code, ordered by code.
group_by(.status)
| map({status: .[0].status, requests: length})
| sort_by(.status)

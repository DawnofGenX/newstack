# Bytes served per calendar day, oldest first.
group_by(.time[0:10])
| map({day: .[0].time[0:10], bytes: (map(.bytes) | add // 0)})
| sort_by(.day)

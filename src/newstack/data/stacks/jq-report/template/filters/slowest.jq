# The five slowest requests, ties broken by path.
sort_by(-.ms, .path)
| .[:5]
| map({method, path, ms})

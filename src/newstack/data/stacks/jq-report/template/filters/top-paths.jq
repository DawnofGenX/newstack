# The five busiest paths, ties broken by path name.
group_by(.path)
| map({path: .[0].path, hits: length})
| sort_by(-.hits, .path)
| .[:5]

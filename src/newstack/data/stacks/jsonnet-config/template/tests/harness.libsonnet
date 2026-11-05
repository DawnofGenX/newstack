// A test harness in plain Jsonnet: results are data, the report is a string.
{
  check(name, ok, detail=''): { name: name, ok: ok, detail: detail },

  equal(name, got, want): {
    name: name,
    ok: got == want,
    detail: if got == want then '' else 'got ' + std.toString(got) + ', want ' + std.toString(want),
  },

  report(results)::
    local failures = [r for r in results if !r.ok];
    std.join('\n', [
      std.join('\n', ['ok   ' + r.name for r in results if r.ok]),
      std.join('\n', ['FAIL ' + r.name + (if r.detail != '' then ' (' + r.detail + ')' else '') for r in failures]),
      '',
      'checks: %d, passed: %d, failed: %d' % [
        std.length(results),
        std.length(results) - std.length(failures),
        std.length(failures),
      ],
    ]),
}

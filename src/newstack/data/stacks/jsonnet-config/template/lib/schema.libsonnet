// Validation rules for a service manifest, expressed as data.
{
  isNonEmptyString(value): std.isString(value) && std.length(value) > 0,

  // Written character by character on purpose: std.findSubstr does not honour
  // '^' and '$' anchors, so a regex that looks right silently matches nothing.
  isNameChar(ch): (ch >= 'a' && ch <= 'z') || (ch >= '0' && ch <= '9') || ch == '-',

  isServiceName(value): std.isString(value) && std.length(value) > 0 && std.length(value) <= 63
                        && value[0] >= 'a' && value[0] <= 'z'
                        && std.foldl(function(acc, ch) acc && self.isNameChar(ch),
                                     std.stringChars(value), true),

  validate(manifest)::
    local services = if std.objectHas(manifest, 'services') then manifest.services else [];
    local names = [s.name for s in services];
    local problems(service) =
      local prefix = if std.objectHas(service, 'name') then service.name else '<unnamed>';
      [
        if !self.isNonEmptyString(service.name) then prefix + ': name must be a non-empty string',
        if !self.isServiceName(service.name) then prefix + ': name must be lower-case letters, digits and dashes',
        if !self.isNonEmptyString(service.image) then prefix + ': image must be a non-empty string',
        if !std.isNumber(service.port) || service.port < 1 || service.port > 65535 then
          prefix + ': port must be between 1 and 65535',
        if !std.isNumber(service.replicas) || service.replicas < 1 || service.replicas > 20 then
          prefix + ': replicas must be between 1 and 20',
      ] + [
        if !std.isString(service.env[k]) then prefix + ': env.' + k + ' must be a string'
        for k in std.objectFields(if std.objectHas(service, 'env') then service.env else {})
      ];
    local errors = [e for service in services for e in problems(service) if e != null];
    local duplicates = [name for name in std.set(names) if std.length([n for n in names if n == name]) > 1];
    {
      ok: std.length(errors) == 0 && std.length(duplicates) == 0 && std.length(services) > 0,
      errors: errors + ['duplicate service name: ' + name for name in duplicates] +
              (if std.length(services) == 0 then ['manifest must declare at least one service'] else []),
    },
}

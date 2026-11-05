# {{ title }}

An authorisation decision that can be read out loud: who asked, which role they
hold *here*, which rule won, and why every other rule lost.

```console
$ {{ npm_name }} decide --policy fixtures/policy.json \
      --subject alice --action docs:write --resource project:acme/doc:42
request   alice wants docs:write on project:acme/doc:42
roles     editor@project:acme, viewer@project:acme
decision  ALLOW  by allow-write
  -      allow  allow-read                action docs:write is not docs:read
  MATCH  allow  allow-write               no condition
  -      allow  allow-comment             action docs:write is not comments:create
  -      deny   deny-secret               resource pattern **/secret does not cover project:acme/doc:42
```

## The rules the engine keeps

1. **Deny wins.** A matching deny outranks any number of matching allows, and the
   decision names the deny. If two denies match, the lowest rule id wins so the
   sentence is the same on every run.
2. **Everything else is denied by default.** "No rule matched" is its own
   decision, not a quietly allowed one.
3. **A role is held on a scope.** `editor on project:acme` applies to
   `project:acme` and everything under it, and to nothing else. The trace says
   `holds none of the roles editor here` when the scope is what excluded a rule.
4. **`*` matches one segment, `**` matches any number of them.** `project:*`
   matches the segment `project:acme` but not `project:acme/doc:42`; write
   `project:**` for a subtree. This is the wildcard that silently never matches,
   and `check` warns when a `.../*` rule sits above deeper rules.
5. **A missing attribute is not a match.** `$resource.owner == $subject.id` is
   false when either side is absent, and the trace says which one was missing.
   An unevaluatable condition never falls through to allowed.
6. **The policy is validated before it decides anything.** Unknown roles, keys,
   effects and operators, duplicate rule ids, rules that name nobody, and
   inheritance cycles are all errors at load time, with the policy path in the
   message. A cycle is an error because it has no fixed point.

## Install

```console
uv venv --allow-existing .venv
uv pip install --python .venv/bin/python -e . pytest ruff
.venv/bin/python -m {{ package_name }} demo
```

## Commands

```
{{ npm_name }} decide --policy FILE --subject NAME --action ACTION --resource PATH
                      [--subject-attr KEY=VALUE]... [--resource-attr KEY=VALUE]... [--json]
{{ npm_name }} check --policy FILE
{{ npm_name }} demo
{{ npm_name }} selftest
```

`decide` exits 0 for allow and 1 for deny — including the default deny — so it
works as a gate. `check` exits 0 when it has no findings and 1 when it does, and
it prints every rule's inheritance so a reviewer can see the graph.

## The policy file

```json
{
  "roles": {"editor": {"inherits": ["viewer"]}},
  "assignments": [{"subject": "alice", "role": "editor", "scope": "project:acme"}],
  "rules": [
    {"id": "allow-write", "effect": "allow", "action": "docs:write",
     "resource": "project:acme/*", "roles": ["editor"]},
    {"id": "deny-secret", "effect": "deny", "action": "docs:*",
     "resource": "**/secret", "subjects": ["*"]}
  ]
}
```

A rule matches when the action pattern, the resource pattern, the role (held on
this resource, inherited roles included), the subject list and the condition all
match. `subjects: ["*"]` means every subject. A condition is
`{"left": ..., "op": ..., "right": ...}` where operands are literals,
`$subject.<attr>` or `$resource.<attr>`, and the operator is one of `eq`, `neq`,
`in`, `not_in`, `lt`, `lte`, `gt`, `gte`, `present`, `absent`.

## What it refuses to do

- It does not guess an unassigned subject is an admin: no assignment means the
  default deny, and the trace says so.
- It does not treat a failed condition as "no opinion": the rule is reported as
  not matching.
- It does not read attributes from the environment or the clock; every input is
  on the command line, so a decision can be reproduced later.
- It does not store or log: this is the decision, an audit log is a different
  component that should record `--json` output.

## Layout

```
src/{{ package_name }}/patterns.py    segments, * and **, scopes
src/{{ package_name }}/conditions.py   operators, missing attributes
src/{{ package_name }}/policy.py      parsing and validation
src/{{ package_name }}/engine.py      decide(), the trace, deny precedence
src/{{ package_name }}/cli.py         decide / check / demo / selftest
fixtures/policy.json                  the six-scenario demo policy
```

## Tests

```
.venv/bin/python -m pytest        # unit tests per module
.venv/bin/python -m {{ package_name }} selftest
PY=.venv/bin/python bash smoke.sh # the CLI, end to end
```

# {{ title }}

{{ description }}

A schema diff is easy to produce and hard to trust. This tool answers one narrow
question — *can a document that validated against the old schema fail against the
new one, or can a member a reader relied on disappear?* — and then proves every
"yes" with a real document.

## Quick start

    uv venv --allow-existing .venv
    uv pip install --python .venv/bin/python -e . pytest ruff

    .venv/bin/python -m {{ package_name }} diff
    .venv/bin/python -m {{ package_name }} demo

`diff` compares `fixtures/v1.json` with `fixtures/v2.json` by default:

    breaking additional-properties-closed $  documents carrying undeclared members are now invalid
    breaking required-added             $  'currency' is required now; documents written against the old schema omit it
    breaking maximum-added              $.amount  maximum 1000000 now bounds documents
    safe     property-added             $.currency  a new optional member
    breaking property-removed           $.note  the member is gone from the contract; a reader that uses it gets nothing
    breaking enum-value-removed         $.type  'order.paid' is no longer allowed
    5 breaking, 0 risky, 1 safe -> breaking

Each line is `level`, `rule`, JSON-path, and the reason. The path is the member,
so a reviewer knows what to look at without opening the schema.

`demo` proves the breaking findings:

    schema evolution: v1 -> v2 is breaking, 5 breaking change(s) to prove

    breaking additional-properties-closed   extra-member.json      $.meta: unexpected member 'meta'
    breaking enum-value-removed             retired-type.json      $.type: 'order.paid' is not one of ['order.created']
    breaking maximum-added                  over-limit.json        $.amount: above the maximum 1000000
    reader   property-removed               (reader)               the member is gone from the contract; a reader that uses it gets nothing
    breaking required-added                 missing-currency.json  $: missing required member 'currency'
    proof    4 validator claim(s) shown by a real document, 1 reader claim(s), 0 unproven

    also     v1 -> v3 is compatible (0 breaking), v1 -> v4 is risky (4 risky)

The evidence is not a template string: each witness is loaded from
`fixtures/documents/`, validated against the old schema (must pass) and the new
one (must fail), and the first failure is quoted. A witness that passes the new
schema is reported as `unproven` and the demo exits 1 — the tool would rather
admit it than cry wolf.

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | no breaking change (or `--strict` and no risky change either) |
| 1 | breaking change found, or a breaking claim the demo could not prove |
| 2 | unusable input: a missing file, broken JSON, or a document that is not a schema |

## The traps this stack encodes

1. **Adding a required member breaks every writer.** `diff` reports
   `required-added` at the parent path, because the failure happens on the
   object, not on the new member.
2. **Removing a property breaks readers, and no document can prove it.** The old
   documents still validate. This is why the rule is labelled `reader`: the
   evidence is the contract, not a failing document.
3. **A changed pattern is undecidable.** `^ord_[0-9]+$` → `^ORD-[0-9]+$` is
   breaking in practice and unprovable in general, so it is `risky` — it fails
   under `--strict`, not by default.
4. **Widening a type is safe for writers and work for readers.** `string` →
   `["string", "integer"]` is `type-widened` (safe); the reverse is
   `type-narrowed` (breaking); a straight replacement is one `type-changed`
   finding, not two.
5. **A new `default` changes behaviour without changing validity.** Reported as
   `risky` (`default-added`), because a reader that never saw the field will now
   see a value.
6. **Closing `additionalProperties` breaks documents that carried extras.** The
   rule is `additional-properties-closed`, and the demo's witness is a document
   with a `meta` member that was legal under the old schema.
7. **Documentation keys are ignored.** `description`, `title`, `examples`,
   `$comment` change nothing about what validates, so they produce no findings —
   a diff that screams about prose gets ignored.
8. **The order of findings is deterministic.** Findings are sorted by
   `(path, rule)`, so two runs print byte-identical reports and a golden file is
   a usable test.

## Layout

| path | what it holds |
| ---- | ------------- |
| `src/{{ package_name }}/schema.py` | the loader, the small validator, `$ref` resolution |
| `src/{{ package_name }}/compare.py` | one method per rule family, and the report |
| `src/{{ package_name }}/demo.py` | the witnesses, and the proof loop |
| `src/{{ package_name }}/cli.py` | `diff`, `demo`, `selftest` |
| `src/{{ package_name }}/selftest.py` | 63 checks over the rules and the fixtures |
| `fixtures/v1.json` … `v4.json` | old, breaking, additive, and undecidable pairs |
| `fixtures/documents/` | the witnesses, all valid under `v1` |

## What this is not

It is not a JSON Schema implementation. The validator covers the keywords the
fixtures use, so the proof means "this document fails for the reason quoted",
not "this document is invalid according to the 2020-12 specification". It also
does not compare two schemas for equivalence, and it does not decide whether a
pattern change is safe — nobody can.

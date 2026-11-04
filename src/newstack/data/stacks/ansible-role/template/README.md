# {{ title }}

An Ansible role that installs a small wc-style counter, scaffolded by
[newstack](https://github.com/DawnofGenX/newstack). It exercises the shape a
real role needs — defaults, vars, a task file with validation, a template, a
file to copy, a handler, an assert-based verification playbook — and installs
everything under one prefix so a test run cannot touch the host.

## Requirements

- `ansible-core` 2.17 or newer (`ansible-playbook` on `PATH`)

## What it does

- validates `textstat_columns` against the columns it can report;
- creates `{{! textstat_prefix }}/bin` and `.../etc`;
- copies `files/textstat` to `.../bin/textstat` (mode `0755`);
- renders `templates/textstat.conf.j2` to `.../etc/textstat.conf` and notifies
  the "Stamp the install" handler;
- writes `.../etc/.installed` from that handler, so a second run that changes
  nothing also runs no handler.

| Variable | Default | Meaning |
| --- | --- | --- |
| `textstat_prefix` | `~/.local/textstat` | where everything is installed |
| `textstat_separator` | `" "` | printed between the figures |
| `textstat_columns` | `lines,words,bytes` | which figures to print, in order |
| `textstat_binary_mode` | `0755` | mode of the installed counter |
| `textstat_config_mode` | `0644` | mode of the rendered config |

## Try it

```console
$ ansible-playbook -i localhost, tests/playbook.yml
$ {{! textstat_prefix }}/bin/textstat README.md
```

Counts come from `wc`, so they agree with it by construction: a file of two
lines, three words and 17 bytes prints `2 3 17`.

## Verify

```console
$ ansible-playbook -i localhost, tests/playbook.yml -e textstat_prefix=$PWD/.play/prefix
$ ansible-playbook -i localhost, tests/verify.yml -e textstat_prefix=$PWD/.play/prefix
```

The second run of the playbook reports `changed=0` — the handler only fires
when the rendered configuration actually changes.

## Layout

```
defaults/main.yml      knobs a user overrides
vars/main.yml          the role's own constants
tasks/main.yml         validation, install tree, copy, template
handlers/main.yml      the install stamp
templates/             textstat.conf.j2
files/                 textstat
meta/main.yml          Galaxy metadata
tests/                 playbook.yml (apply) and verify.yml (assert)
```

## Licence

MIT — see [LICENSE](LICENSE).

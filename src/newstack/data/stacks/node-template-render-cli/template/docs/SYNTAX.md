# Template syntax

A template is plain text. A placeholder is a key wrapped in double braces:

```text
Hello, {{!name}}! You have {{!count}} new {{!noun}}.
```

The context file is JSON whose keys line up with those names:

```json
{"name": "Ada", "count": 2, "noun": "messages"}
```

Rendering HTML-escapes every substituted value:

```sh
node src/cli.js template.tpl context.json
# Hello, Ada! You have 2 new messages.
```

A missing key renders as an empty string, and an unterminated placeholder is a
syntax error (exit code 2).

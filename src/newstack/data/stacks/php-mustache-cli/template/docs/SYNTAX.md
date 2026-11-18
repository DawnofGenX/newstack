# Tag syntax

| Tag | Meaning |
| --- | --- |
| `{{!! a comment }}` | dropped from the output |
| `{{!name}}` | HTML-escaped variable |
| `{{!{name}}}` | raw variable |
| `{{!&name}}` | raw variable, alternate form |
| `{{!#items}}...{{!/items}}` | section: repeated for a list, once for a map |
| `{{!^items}}...{{!/items}}` | inverted section: rendered when falsy or empty |
| `{{!user.name}}` | dotted member lookup |
| `{{!.}}` | the current item inside a list section |

Example:

```
{{!! a greeting }}
Hi {{!name}}, you have {{!#items}}{{!.}} {{!/items}}
```

With `{"name": "Ada", "items": ["mail", "code"]}` that renders
`Hi Ada, you have mail code `.

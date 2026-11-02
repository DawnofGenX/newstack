# {{ title }}

{{ description }}

Zero-build static site: plain HTML, CSS and JavaScript. Push to `main` and the
included workflow publishes it to GitHub Pages.

## Preview locally

```bash
python3 -m http.server 8000
# or: npx serve .
```

## Publish

1. Push this repository to GitHub.
2. Settings → Pages → Source: **GitHub Actions**.
3. The next push to `main` deploys it.

Generated with [newstack](https://github.com/DawnofGenX/newstack).

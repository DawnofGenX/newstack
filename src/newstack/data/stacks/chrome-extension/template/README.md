# {{ title }}

{{ description }}

A Manifest V3 Chrome extension scaffold: a popup, a background service worker,
a content script, a Vite build and Vitest tests over the pure logic.

- `manifest.json` — MV3 manifest (popup, service worker, content script, `storage`).
- `src/popup/` — popup UI; `main.ts` wires the DOM to `src/lib/counter.ts`.
- `src/lib/counter.ts` — pure counter logic (no `chrome.*` calls), unit tested.
- `src/background.ts` — service worker; seeds `chrome.storage.local` on install.
- `src/content.ts` — content script; marks `document.body` on every page.

## Requirements

- Node.js {{ node_version }} or newer, {{ package_manager_prereq }}.
- Chrome (or any Chromium browser) to load the unpacked build.

## Install

```sh
{{ package_manager_install }}
```

## Develop

```sh
{{ package_manager_run }} dev
```

`vite` rebuilds on save. For a live extension, load `dist/` as an unpacked
extension (see below) while `{{ package_manager_run }} dev` is running, then reload the
extension after changes.

## Test

```sh
{{ package_manager_test }}         # vitest run (jsdom)
{{ package_manager_run }} typecheck
```

## Build

```sh
{{ package_manager_run }} build
```

Output lands in `dist/`: `manifest.json`, `background.js`, `content.js` and the
popup assets.

## Pack

```sh
{{ package_manager_run }} pack
```

Builds and writes `extension.zip` from the contents of `dist/` (the manifest
sits at the zip root, which is what the Chrome Web Store expects).

## Load it in Chrome

1. Open `chrome://extensions`.
2. Turn on **Developer mode** (top right).
3. Click **Load unpacked** and select the `dist/` folder.
4. Pin the extension and click its icon to open the popup.

After rebuilding, press the reload button on the extension card.

## Project layout

```
manifest.json
src/
  background.ts
  content.ts
  lib/counter.ts
  lib/counter.test.ts
  popup/index.html
  popup/main.ts
vite.config.ts
tsconfig.json
```

## License

MIT — see [LICENSE](./LICENSE).

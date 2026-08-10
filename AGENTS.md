# AGENTS.md

## Cursor Cloud specific instructions

This repository is a **single static client-side web app**: an "8 Ball Pool" browser game (vanilla HTML/CSS/ES-module JS). There is **no backend, no database, and no package manager** (no `package.json` / lockfile). Python 3 and Node.js are preinstalled in the environment and are all that is needed.

### Run the app (dev)
Serve the repo root over HTTP (ES modules + service worker + PWA require HTTP, not `file://`):

```bash
python3 -m http.server 8080 --bind 0.0.0.0
```

Then open `http://127.0.0.1:8080/index.html` → click `▶ ИГРАТЬ` to start the game. `./serve-ios.sh [port]` does the same thing (default port 8080) and prints a LAN URL for iPhone testing. The UI is in Russian.

### Build (optional, production-like)
```bash
node scripts/build.mjs
```
Non-obvious caveats:
- It fetches `esbuild` on demand via `npx` (needs npm-registry network access the first time).
- It **overwrites the committed `play.html`, `pool-v5.html`, `pool-v51.html`** with regenerated standalone bundles, and writes `dist/` (gitignored). Output is deterministic, so a clean checkout usually produces no diff — but check `git status` and avoid committing regenerated bundles unless intended.
- Running the build is **not required** to develop or test locally; serving the repo root is enough.

### Lint / test
There are **no lint or automated test setups** in this repo (no ESLint/Prettier, no test framework, no CI test/lint job — CI only deploys to GitHub Pages). Verify changes by serving the app and testing gameplay in the browser.

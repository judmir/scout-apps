# scout-apps

Standalone, static previews from the nightly startup scout (Judi's Validation Ideas). Served by GitHub Pages from the
`gh-pages` branch, one folder per night's winner:

```
https://judmir.github.io/scout-apps/<date>-<slug>/demo/      clickable demo of the night's POC (static, mocked data)
https://judmir.github.io/scout-apps/<date>-<slug>/landing/   validation page preview built from the night's brief
https://judmir.github.io/scout-apps/apps.json                what exists, per night (read by Validation Ideas)
```

Everything here is a preview: `noindex,nofollow`, `robots.txt` disallows all, no sign-ups, no email capture, no payments,
no analytics, no third-party requests (no external fonts or CDNs).

## What's in this repo

- `main`: the reusable pieces only.
  - `templates/landing/index.html`: the landing template (inline CSS/JS, strict CSP, system fonts). Buttons only record a
    click in `localStorage` and show "Not launched yet".
  - `tools/make-landing.py`: fills the template from a brief's `## Validation page proposal (winner p-XXX…)` section.
  - `tools/make-index.py`: writes the noindex root `index.html`, `robots.txt` and `.nojekyll` from `apps.json`.
- `gh-pages`: built output only (demo `out/` folders, generated landings, `apps.json`, root index). No app source, no
  server routes, no keys. The POC repos themselves stay private.

## How a night gets published

`validation-ideas/scripts/publish-scout-apps.sh <date>` (called by `scripts/nightly-publish.sh`):

1. Finds the night's winner in the brief and its POC at `startup-research/poc/*-<date>/`.
2. Demo: if the POC's `package.json` has a `demo:static` script, runs it with `DEMO_BASE_PATH=/scout-apps/<date>-<slug>/demo`
   and `DEMO_OUT=<dir>`. The script must produce a static export with no API routes, no AI calls and no keys; imports
   replay recorded results labelled "Mocked: sample import". No `demo:static` → no demo, and `apps.json` records why.
3. Landing: `tools/make-landing.py` from the brief.
4. Scans the built files for key-like strings (`sk-ant`, `ANTHROPIC`, tokens, JWTs, private keys …) and refuses to push on a hit.
5. Commits to `gh-pages` (new commit, never force) and checks the URLs are live.

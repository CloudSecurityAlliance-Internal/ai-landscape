# GitHub Pages Deployment

The web app (`web/`) is a static Astro 4 site deployed via GitHub Pages.

## How it works

- `.github/workflows/deploy-web.yml` triggers on push to `main`
- Runs `npm ci` + `npm run build` inside `web/`
- Uploads `web/dist` as a Pages artifact
- Deploys via `actions/deploy-pages`

## GitHub Repo Settings (one-time manual setup)

In **Settings → Pages**:
- Source: **GitHub Actions** (not "Deploy from a branch")

## Astro config behavior

- `site` is always set to the production URL for canonical links and sitemaps
- `base` is set to `/ai-landscape` only during GitHub Actions builds (`GITHUB_ACTIONS=true`)
- Local dev serves from `http://localhost:4321/` with no base prefix

## URLs

| Environment | URL |
|---|---|
| Production | https://cloudsecurityalliance-internal.github.io/ai-landscape/ |
| Local dev | http://localhost:4321/ |

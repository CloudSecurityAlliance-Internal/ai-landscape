# Cloudflare Pages Deployment

The web app (`web/`) is a static Astro 4 site deployed via Cloudflare Pages.

## Cloudflare Pages Dashboard Settings

| Setting | Value |
|---|---|
| Root directory | `web` |
| Build command | `npm run build` |
| Build output directory | `dist` |
| Node version | `20` |

## Notes

- `output: "static"` in `astro.config.mjs` — no server adapter needed.
- No `base` path is set. The site is served from the domain root.
- `site` URL is intentionally omitted until the final domain is confirmed. Set it in `astro.config.mjs` once known (used for canonical URLs and sitemaps).
- `.github/workflows/deploy-web.yml` (GitHub Pages workflow) is retained for reference but is not used by Cloudflare Pages.

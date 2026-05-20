# AI Landscape — System Design

A Cloud Security Alliance project mapping the AI ecosystem, modeled after [landscape.cncf.io](https://landscape.cncf.io).

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                  SOURCE OF TRUTH                         │
│            data/landscape.yaml  (Git repo)              │
└──────────┬────────────────────────┬─────────────────────┘
           │                        │
    CI build (on merge)      reads at startup
           │                        │
           ▼                        ▼
┌──────────────────┐     ┌──────────────────────┐
│   Astro static   │     │  TypeScript MCP       │
│   site (HTML)    │     │  server               │
│                  │     │                       │
│  Human browsing  │     │  AI agent consumption │
│  read-only       │     │  read-only            │
└──────────────────┘     └──────────────────────┘
      Cloudflare               Fly.io / Railway
      Pages / GH Pages         (small container)

           ▲
    opens GitHub PRs
           │
┌──────────────────┐
│  Python agent    │
│  (Claude API)    │
│                  │
│  Researches and  │
│  proposes new    │
│  entries         │
└──────────────────┘
    Runs on schedule
    (GitHub Actions cron)

Developer reviews PR → merges → CI triggers rebuild + redeploy
```

## Key Principles

- **`data/landscape.yaml` is the single source of truth.** Neither the web frontend nor the MCP server have their own independent copy of the data.
- **Web and MCP are read-only.** All writes go through Git (PR review) before reaching either service.
- **Agent writes are auditable.** The Python agent opens GitHub PRs — every change has a diff, a commit, and a reviewer. No agent writes directly to production.
- **No runtime database.** The static site bakes data in at build time; the MCP server loads it at startup. No connection pooling, migrations, or backups needed.

## Components

| Component | Language/Stack | Purpose | Deployment |
|-----------|---------------|---------|-----------|
| `data/landscape.yaml` | YAML | Source of truth for all landscape entries | Git repo |
| Web frontend | Astro (static) | Human-readable landscape map | Cloudflare Pages / GitHub Pages |
| MCP server | TypeScript (`@modelcontextprotocol/sdk`) | AI-readable landscape API | Fly.io / Railway |
| Agent | Python (Claude API) | Researches and proposes new/updated entries | GitHub Actions cron |
| CI/CD | GitHub Actions | Validates YAML, builds site, deploys | GitHub |

## Data Flow

1. **Read path (web):** User opens site → served pre-built static HTML (generated from YAML at last CI run)
2. **Read path (MCP):** AI queries MCP server → server reads from YAML loaded at startup → returns structured data
3. **Write path:** Agent researches ecosystem → generates YAML entry → opens GitHub PR → developer reviews → merges → CI rebuilds site + redeploys MCP server

## License

AGPL-3.0. All dependencies must be AGPL-compatible (MIT, Apache 2.0, GPL, LGPL are all compatible).

# AI Landscape — Design Spec

**Date:** 2026-05-19
**Project:** CSA AI Landscape
**License:** AGPL-3.0

---

## Overview

A Cloud Security Alliance project mapping the general AI ecosystem, modeled after [landscape.cncf.io](https://landscape.cncf.io). Provides two read-only interfaces to a shared, Git-backed data file:

- **Web frontend** — human-readable dense grid, built with Astro (static site)
- **MCP server** — AI-readable API, built with TypeScript and `@modelcontextprotocol/sdk`

All writes go through Git PRs. A Python agent running on a schedule autonomously proposes new entries. Developers review and merge PRs; CI rebuilds and redeploys both services on merge.

---

## System Architecture

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

### Key Principles

- `data/landscape.yaml` is the single source of truth. No separate runtime database.
- Web and MCP are strictly read-only. All writes go through Git PR review.
- Agent writes are fully auditable — every change is a diff with source URLs.
- No runtime database: the static site bakes data in at build time; the MCP server loads it at startup.

### Components

| Component | Stack | Purpose | Deployment |
|-----------|-------|---------|-----------|
| `data/landscape.yaml` | YAML | Source of truth | Git repo |
| Web frontend | Astro (static) | Human-readable landscape map | Cloudflare Pages / GitHub Pages |
| MCP server | TypeScript (`@modelcontextprotocol/sdk`) | AI-readable landscape API | Fly.io / Railway |
| Agent | Python + Claude API | Proposes new/updated entries via PRs | GitHub Actions cron |
| CI/CD | GitHub Actions | Validates, builds, deploys | GitHub |

---

## Taxonomy

12 top-level categories, function-based. Categories and subcategories are defined in `landscape.yaml` alongside entries.

| Category | Description |
|----------|-------------|
| Foundation Models | LLMs, multimodal, reasoning, code models, open weights vs. proprietary |
| Agentic Harnesses | Agent frameworks, orchestration, multi-agent systems, memory |
| Protocols & Standards | MCP, A2A, OpenAI API spec, interoperability standards |
| MCP Servers & Marketplaces | MCP server registries, tool marketplaces, plugin ecosystems |
| Data & Knowledge | Vector databases, RAG frameworks, data pipelines, embeddings |
| Training & Fine-Tuning | Training frameworks, RLHF tooling, fine-tuning platforms, MLOps |
| Inference & Deployment | Inference APIs, model hosting, edge deployment, serving infra |
| Observability & Evals | Tracing, benchmarking, red-teaming, testing, LLM-as-judge |
| Security & Governance | AI governance frameworks, risk & compliance, model auditing, privacy |
| Developer Tools | AI-assisted IDEs, coding assistants, prompt engineering, CLI tools |
| Platforms & Applications | Enterprise AI platforms, vertical applications, no-code AI builders |
| Research & Benchmarks | Model leaderboards, safety research orgs, academic benchmarks |

---

## Data Model

### landscape.yaml structure

```yaml
categories:
  - id: agentic-harnesses
    name: Agentic Harnesses
    subcategories:
      - id: multi-agent
        name: Multi-Agent Frameworks
      - id: single-agent
        name: Single-Agent Frameworks

entries:
  - id: claude-code                    # unique slug, kebab-case
    name: Claude Code
    category: agentic-harnesses        # must match a category id
    subcategory: single-agent          # must match a subcategory id
    organization: Anthropic
    description: "Agentic AI coding assistant that operates in your terminal"
    logo: logos/claude-code.svg        # path relative to data/logos/
    website: https://claude.ai/code
    github: null                       # null if proprietary
    license: proprietary               # SPDX identifier or "proprietary" (e.g. MIT, Apache-2.0, GPL-3.0, AGPL-3.0, proprietary)
    pricing: freemium                  # free | freemium | paid | enterprise
    api_available: true
    tags: [coding, cli, agentic]
    added: 2026-05-19
    updated: 2026-05-19
```

### Required fields
`id`, `name`, `category`, `organization`, `description`, `website`, `license`, `pricing`, `added`, `updated`

### Optional fields
`subcategory`, `logo`, `github`, `api_available`, `tags`

### Field notes
- **`license`** — use SPDX identifiers where possible (`MIT`, `Apache-2.0`, `GPL-3.0`, `AGPL-3.0`, etc.) or `proprietary` for closed-source tools. This is orthogonal to pricing — a tool can be open-source with a paid hosted tier, or proprietary but free.
- **`pricing`** — captures cost model only: `free` = no-cost; `freemium` = free tier + paid tier; `paid` = paid only; `enterprise` = contact-sales pricing. Does not imply anything about source availability.
- **`api_available`** — true if the tool exposes a programmatic API (useful filter for developers)
- **`tags`** — free-form, enables cross-category discovery (e.g., all entries tagged `security`)
- **`added` / `updated`** — enables "recently added" on the web UI and signals the agent which entries need a refresh

---

## Web Frontend

**Stack:** Astro (static site generator, MIT) + Pagefind (client-side search, MIT)

**Layout:** Dense grid, similar to landscape.cncf.io — maximum entries visible per screen. Entries are grouped by category, displayed as compact tiles with logo and name. Click-to-expand shows full entry detail (description, links, tags, pricing, license).

**Features:**
- Category filter bar (top navigation)
- Tag filter (sidebar or dropdown)
- Client-side full-text search via Pagefind (no server required)
- "Recently added" indicator on entries added in the last 30 days
- Responsive — usable on mobile

**Build:** Astro reads `data/landscape.yaml` at build time via a content collection. No JavaScript is shipped for the grid itself — only the search bar is an interactive island. Fast load, fully indexable by search engines.

**Deployment:** Cloudflare Pages or GitHub Pages (static hosting, no server required).

---

## MCP Server

**Stack:** TypeScript, `@modelcontextprotocol/sdk` (MIT), reads `landscape.yaml` at startup.

**Exposed tools (read-only):**

| Tool | Arguments | Returns |
|------|-----------|---------|
| `list_categories` | — | All categories with entry counts |
| `list_entries` | `category?`, `subcategory?`, `tags?`, `pricing?`, `license?`, `api_available?` | Filtered entries (id, name, description, category, tags) |
| `get_entry` | `id` | Full detail for one entry (all fields) |
| `search_entries` | `query` | Full-text search across name, description, organization, tags |
| `get_stats` | — | Total entries, per-category counts, last-updated date |

No write tools are exposed. The MCP server enforces the read-only constraint at the protocol level.

**Deployment:** Small container (Fly.io or Railway). Redeployed by CI on every merge to main so it always reflects the latest YAML.

---

## Python Agent

**Stack:** Python, Claude API (`claude-sonnet-4-6`), Pydantic (validation), PyGitHub (PR creation).

**Workflow:**

1. **Choose target** — pick a category not recently refreshed (or accept a specific category/tool as input)
2. **Research** — web search for tools in the category; fetch GitHub metadata (stars, license, activity) via GitHub API
3. **Generate entries** — populate all YAML fields for new tools; check changed fields for existing entries
4. **Validate** — schema-check against a Pydantic model; skip any entry missing required fields
5. **Open PR** — append new entries / update changed fields in `landscape.yaml`; open GitHub PR titled `agent: add N entries to <category>` with source URLs in the description

**PR contents:** Structured YAML diff + list of each change with source URL, so a developer can spot-check accuracy in ~30 seconds.

**Schedule:** Weekly GitHub Actions cron job, rotating through categories so every category is refreshed roughly monthly.

---

## CI/CD Pipeline

**On PR open (agent or human):**
1. Validate `landscape.yaml` against Pydantic schema (same model the agent uses)
2. Check for duplicate entry `id` values
3. Verify all referenced logo files exist in `data/logos/`

PR is blocked from merge if any check fails.

**On merge to main:**
1. Build Astro static site
2. Deploy to Cloudflare Pages (or GitHub Pages)
3. Redeploy MCP server container

**On schedule (weekly):**
1. Trigger agent run for the next category in rotation
2. Agent opens PR if it finds new or changed entries; no PR if nothing changed

---

## Repository Structure (proposed)

```
ai-landscape/
├── data/
│   ├── landscape.yaml          # source of truth
│   └── logos/                  # SVG logos for entries
├── web/                        # Astro static site
│   ├── src/
│   │   ├── pages/
│   │   └── components/
│   └── astro.config.mjs
├── mcp/                        # TypeScript MCP server
│   ├── src/
│   │   └── server.ts
│   └── package.json
├── agent/                      # Python agent
│   ├── agent.py
│   ├── schema.py               # Pydantic models
│   └── requirements.txt
├── .github/
│   └── workflows/
│       ├── ci.yml              # PR validation
│       ├── deploy.yml          # build + deploy on merge
│       └── agent.yml           # weekly agent cron
├── docs/
│   ├── system-design.md
│   └── superpowers/specs/
├── shell.nix
├── CLAUDE.md
└── README.md
```

---

## Out of Scope (v1)

- User accounts or community submissions (write access is agent + developers only)
- Entry ratings, reviews, or comments
- Real-time data (pricing/GitHub stats are refreshed by agent on schedule, not live)
- A separate REST API (the MCP server is the programmatic interface; Astro's static output serves the web)

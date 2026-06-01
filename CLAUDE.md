# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

`ai-landscape` is the **CSA AI Security Landscape** — a vendor-neutral, continuously updated market map for AI security and observability, modeled after [landscape.cncf.io](https://landscape.cncf.io). It is a Cloud Security Alliance (CSA) project defined by RFC-001 (`docs/rfc-001-vision.md`).

License: **AGPL-3.0**. All dependencies and integrations must be AGPL-compatible. Network use counts as distribution under AGPL.

## Status

This project is in active development. Phases 1–3 (data foundation, MCP server, and Astro web frontend) are complete and merged. Core conventions are established — see Key Conventions below. Check recent commits before assuming anything beyond what's documented here.

## Architecture

`data/landscape.yaml` is the single source of truth. No runtime database.

- **Web** — Astro 4 static site (reads YAML at build time) → Cloudflare Pages
- **MCP server** — TypeScript + `@modelcontextprotocol/sdk` (reads YAML at startup) → Fly.io container
- **Agent** — Python 3.13 + Claude API (proposes new entries via GitHub PRs) → GitHub Actions cron
- **CI/CD** — GitHub Actions (validates YAML on PR, builds + deploys on merge to main)

All writes go through Git PR review. Agent never writes directly to production.

## Tech Stack

- `agent/` — Python 3.13, Pydantic v2, PyYAML, PyGitHub, pytest
- `mcp/` — TypeScript, `@modelcontextprotocol/sdk`, js-yaml, vitest
- `web/` — Astro 4, Pagefind (client-side search), js-yaml
- CI/CD — GitHub Actions

## Repository Structure

```
data/landscape.yaml       — source of truth (categories + entries)
data/logos/               — SVG logos referenced by entries
agent/                    — Python schema, validator, research agent
mcp/src/                  — TypeScript MCP server (5 read-only tools)
web/src/                  — Astro static site (dense grid + filter + search)
.github/workflows/        — ci.yml, deploy.yml, agent.yml
docs/system-design.md     — architecture overview
docs/superpowers/plans/   — implementation plan (task-by-task with code)
docs/superpowers/specs/   — design spec (taxonomy, data model, component detail)
```

## Implementation Status

- ✅ Phase 1 Task 1 — `agent/schema.py` (Pydantic models, RFC-001 fields)
- ✅ Phase 1 Task 2 — `data/landscape.yaml` (AI security taxonomy, 13 categories, 13 sample entries)
- ✅ Phase 1 Task 3 — `agent/validate.py` + CI workflow
- ✅ Phase 2 — MCP server (`mcp/`)
- ✅ Phase 3 — Astro web frontend (`web/`)
- 🔄 RFC-001 branch — `feature/rfc-001-agentic-mvp`
  - ✅ Commit set 1: RFC-001 taxonomy, extended schema, updated tests
  - ⬜ Commit set 2: Local proposal agent (`agent/propose.py`)
  - ⬜ Commit set 3: MCP type + filter extensions
  - ⬜ Commit set 4: Web UI realignment

See `docs/rfc-001-vision.md` for product vision and `docs/superpowers/plans/2026-05-19-ai-landscape.md` for the original implementation plan.

## Development Commands

```bash
# Python agent (run from agent/)
cd agent && pytest tests/ -v

# MCP server (run from mcp/)
cd mcp && npm test
cd mcp && npm run build

# Web (run from web/)
cd web && npm run dev
cd web && npm run build

# Validate landscape.yaml
cd agent && python validate.py ../data/landscape.yaml
```

## Key Conventions

- `agent/conftest.py` adds `agent/` to `sys.path` so tests can `import schema` etc. without package install
- Entry `id` must be unique kebab-case slug; validated by `LandscapeFile` model validator
- `pricing` enum: `free | freemium | paid | enterprise`
- `vendor_type` enum: `ai-native | cloud-native | hybrid`
- `maestro_layers` — validated against `MAESTRO_LAYERS` set in `schema.py` (hard error on unknown values)
- `aicm_control_families` — validated against `AICM_FAMILIES` set in `schema.py` (hard error on unknown values)
- Logo files go in `data/logos/` (SVG); referenced in YAML as `logo: logos/filename.svg`
- `csa_member` must be verified against the CSA member roster before entries go live
- Landscape taxonomy: 3 areas (`security-for-ai`, `ai-for-security`, `ai-governance-risk`), 13 categories
- Agent proposals go to `agent/proposals/` — never write directly to `data/landscape.yaml`

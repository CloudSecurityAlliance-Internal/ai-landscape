# CSA AI Landscape — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Git-backed AI ecosystem landscape with an Astro static site, TypeScript MCP server, Python agent, and GitHub Actions CI/CD — all driven by a single `data/landscape.yaml` source of truth.

**Architecture:** `data/landscape.yaml` is committed to Git. Astro reads it at build time to generate a static dense-grid site. The TypeScript MCP server loads it at startup. A Python agent opens GitHub PRs proposing new entries. CI validates YAML on every PR; deploy workflow rebuilds and redeploys on merge to main.

**Tech Stack:** Python 3.13 + Pydantic v2 (schema + agent), TypeScript + `@modelcontextprotocol/sdk` (MCP server), Astro 4 + Pagefind (web), GitHub Actions (CI/CD)

---

## File Map

```
data/
  landscape.yaml              — source of truth: categories + entries
  logos/                      — SVG logos referenced by entries

agent/
  schema.py                   — Pydantic models: LandscapeEntry, LandscapeFile
  validate.py                 — CLI: validates landscape.yaml, exits 0 (pass) or 1 (fail)
  research.py                 — Claude API research loop: finds new tools per category
  github_pr.py                — opens GitHub PRs with new/updated entries
  agent.py                    — CLI entry point orchestrating research + PR creation
  requirements.txt
  conftest.py                 — adds agent/ to sys.path for pytest
  tests/
    __init__.py
    test_schema.py
    test_validate.py
    test_research.py

mcp/
  package.json
  tsconfig.json
  Dockerfile
  src/
    landscape.ts              — loadLandscape, listEntries, searchEntries, getStats
    landscape.test.ts         — vitest tests for landscape utilities
    server.ts                 — MCP server with all 5 tools

web/
  package.json
  astro.config.mjs
  public/
    logos/                    — SVG logos served at /logos/<filename>; add files here as entries are added
  src/
    pages/
      index.astro             — main page: header + filter + grid
    components/
      FilterBar.astro         — category filter tab bar
      LandscapeGrid.astro     — sections grouped by category
      EntryTile.astro         — compact tile: logo + name, links to website

.github/
  workflows/
    ci.yml                    — PR validation: schema check + duplicate ID check
    deploy.yml                — on merge: build web + deploy Cloudflare Pages + redeploy MCP
    agent.yml                 — weekly cron: run agent, open PR if new entries found
```

---

## Phase 1: Data Foundation

### Task 1: Data Schema (Pydantic)

**Files:**
- Create: `agent/schema.py`
- Create: `agent/conftest.py`
- Create: `agent/tests/__init__.py`
- Create: `agent/tests/test_schema.py`

- [ ] **Step 1: Write the failing tests**

```python
# agent/tests/test_schema.py
import pytest
from pydantic import ValidationError
from schema import LandscapeEntry, LandscapeFile


def _valid_entry(**overrides):
    base = {
        "id": "test-tool",
        "name": "Test Tool",
        "category": "agentic-harnesses",
        "organization": "Test Org",
        "description": "A test tool for the landscape",
        "website": "https://example.com",
        "license": "MIT",
        "pricing": "free",
        "added": "2026-05-19",
        "updated": "2026-05-19",
    }
    return {**base, **overrides}


def _valid_landscape(**entry_overrides):
    return {
        "categories": [{"id": "agentic-harnesses", "name": "Agentic Harnesses"}],
        "entries": [_valid_entry(**entry_overrides)],
    }


def test_valid_entry():
    entry = LandscapeEntry(**_valid_entry())
    assert entry.id == "test-tool"
    assert entry.pricing == "free"


def test_optional_fields_default():
    entry = LandscapeEntry(**_valid_entry())
    assert entry.tags == []
    assert entry.api_available is False
    assert entry.github is None


def test_invalid_pricing():
    with pytest.raises(ValidationError, match="pricing"):
        LandscapeEntry(**_valid_entry(pricing="unknown"))


def test_missing_required_field():
    data = _valid_entry()
    del data["name"]
    with pytest.raises(ValidationError):
        LandscapeEntry(**data)


def test_valid_landscape():
    lf = LandscapeFile(**_valid_landscape())
    assert len(lf.entries) == 1


def test_duplicate_entry_ids():
    data = _valid_landscape()
    data["entries"].append(_valid_entry())  # same id
    with pytest.raises(ValidationError, match="[Dd]uplicate"):
        LandscapeFile(**data)


def test_unknown_category_rejected():
    with pytest.raises(ValidationError, match="[Uu]nknown category"):
        LandscapeFile(**_valid_landscape(category="does-not-exist"))
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd agent && pip install pydantic PyYAML pytest && pytest tests/test_schema.py -v
```

Expected: `ModuleNotFoundError: No module named 'schema'`

- [ ] **Step 3: Create conftest.py for pytest path setup**

```python
# agent/conftest.py
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
```

```python
# agent/tests/__init__.py
```

- [ ] **Step 4: Implement schema.py**

```python
# agent/schema.py
from pydantic import BaseModel, field_validator, model_validator
from typing import Optional
from datetime import date

_VALID_PRICING = {"free", "freemium", "paid", "enterprise"}


class Subcategory(BaseModel):
    id: str
    name: str


class Category(BaseModel):
    id: str
    name: str
    subcategories: list[Subcategory] = []


class LandscapeEntry(BaseModel):
    id: str
    name: str
    category: str
    subcategory: Optional[str] = None
    organization: str
    description: str
    logo: Optional[str] = None
    website: str
    github: Optional[str] = None
    license: str
    pricing: str
    api_available: bool = False
    tags: list[str] = []
    added: date
    updated: date

    @field_validator("pricing")
    @classmethod
    def validate_pricing(cls, v: str) -> str:
        if v not in _VALID_PRICING:
            raise ValueError(f"pricing must be one of {_VALID_PRICING}, got '{v}'")
        return v


class LandscapeFile(BaseModel):
    categories: list[Category]
    entries: list[LandscapeEntry]

    @model_validator(mode="after")
    def no_duplicate_ids(self) -> "LandscapeFile":
        ids = [e.id for e in self.entries]
        seen, dupes = set(), set()
        for i in ids:
            (dupes if i in seen else seen).add(i)
        if dupes:
            raise ValueError(f"Duplicate entry IDs: {sorted(dupes)}")
        return self

    @model_validator(mode="after")
    def categories_exist(self) -> "LandscapeFile":
        valid_ids = {c.id for c in self.categories}
        for entry in self.entries:
            if entry.category not in valid_ids:
                raise ValueError(
                    f"Entry '{entry.id}' has unknown category '{entry.category}'"
                )
        return self
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd agent && pytest tests/test_schema.py -v
```

Expected: 7 tests pass.

- [ ] **Step 6: Commit**

```bash
git add agent/
git commit -m "feat: add Pydantic schema for landscape entries"
```

---

### Task 2: Seed landscape.yaml

**Files:**
- Create: `data/landscape.yaml`
- Create: `data/logos/.gitkeep`

- [ ] **Step 1: Create seed data**

```yaml
# data/landscape.yaml
categories:
  - id: foundation-models
    name: Foundation Models
    subcategories:
      - id: llm
        name: Large Language Models
      - id: multimodal
        name: Multimodal Models

  - id: agentic-harnesses
    name: Agentic Harnesses
    subcategories:
      - id: multi-agent
        name: Multi-Agent Frameworks
      - id: single-agent
        name: Single-Agent Frameworks

  - id: protocols-standards
    name: Protocols & Standards

  - id: mcp-servers-marketplaces
    name: MCP Servers & Marketplaces

  - id: data-knowledge
    name: Data & Knowledge

  - id: training-fine-tuning
    name: Training & Fine-Tuning

  - id: inference-deployment
    name: Inference & Deployment

  - id: observability-evals
    name: Observability & Evals

  - id: security-governance
    name: Security & Governance

  - id: developer-tools
    name: Developer Tools

  - id: platforms-applications
    name: Platforms & Applications

  - id: research-benchmarks
    name: Research & Benchmarks

entries:
  - id: claude
    name: Claude
    category: foundation-models
    subcategory: llm
    organization: Anthropic
    description: "Anthropic's AI assistant family, optimized for safety and helpfulness"
    website: https://claude.ai
    github: null
    license: proprietary
    pricing: freemium
    api_available: true
    tags: [reasoning, coding, multimodal, safety]
    added: 2026-05-19
    updated: 2026-05-19

  - id: claude-code
    name: Claude Code
    category: agentic-harnesses
    subcategory: single-agent
    organization: Anthropic
    description: "Agentic AI coding assistant that operates in your terminal with full codebase context"
    website: https://claude.ai/code
    github: null
    license: proprietary
    pricing: freemium
    api_available: true
    tags: [coding, cli, agentic]
    added: 2026-05-19
    updated: 2026-05-19

  - id: model-context-protocol
    name: Model Context Protocol
    category: protocols-standards
    organization: Anthropic
    description: "Open protocol for connecting AI models to external data sources and tools"
    website: https://modelcontextprotocol.io
    github: https://github.com/modelcontextprotocol
    license: MIT
    pricing: free
    api_available: true
    tags: [protocol, open-source, tooling, interoperability]
    added: 2026-05-19
    updated: 2026-05-19
```

- [ ] **Step 2: Create logos directory placeholder**

```bash
touch data/logos/.gitkeep
```

- [ ] **Step 3: Validate seed data against schema**

```bash
cd agent && python -c "
import yaml, sys
sys.path.insert(0, '.')
from schema import LandscapeFile
data = yaml.safe_load(open('../data/landscape.yaml'))
lf = LandscapeFile.model_validate(data)
print(f'OK: {len(lf.categories)} categories, {len(lf.entries)} entries')
"
```

Expected: `OK: 12 categories, 3 entries`

- [ ] **Step 4: Commit**

```bash
git add data/
git commit -m "feat: add seed landscape.yaml with 12 categories and 3 starter entries"
```

---

### Task 3: Validation Script + CI Workflow

**Files:**
- Create: `agent/validate.py`
- Create: `agent/tests/test_validate.py`
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Write the failing tests**

```python
# agent/tests/test_validate.py
from pathlib import Path
from validate import validate


def test_validates_real_yaml():
    yaml_path = Path(__file__).parents[2] / "data" / "landscape.yaml"
    assert validate(str(yaml_path)) is True


def test_rejects_missing_required_field(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text(
        "categories:\n  - id: agentic-harnesses\n    name: Agentic Harnesses\n"
        "entries:\n  - id: x\n    name: Only Name\n"
    )
    assert validate(str(bad)) is False


def test_rejects_duplicate_ids(tmp_path):
    bad = tmp_path / "dup.yaml"
    bad.write_text(
        "categories:\n  - id: agentic-harnesses\n    name: Agentic Harnesses\n"
        "entries:\n"
        "  - id: same\n    name: A\n    category: agentic-harnesses\n"
        "    organization: Org\n    description: Desc\n    website: https://a.com\n"
        "    license: MIT\n    pricing: free\n    added: 2026-05-19\n    updated: 2026-05-19\n"
        "  - id: same\n    name: B\n    category: agentic-harnesses\n"
        "    organization: Org\n    description: Desc\n    website: https://b.com\n"
        "    license: MIT\n    pricing: free\n    added: 2026-05-19\n    updated: 2026-05-19\n"
    )
    assert validate(str(bad)) is False
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd agent && pytest tests/test_validate.py -v
```

Expected: `ModuleNotFoundError: No module named 'validate'`

- [ ] **Step 3: Implement validate.py**

```python
# agent/validate.py
#!/usr/bin/env python3
import sys
import yaml
from pathlib import Path
from pydantic import ValidationError
from schema import LandscapeFile


def validate(yaml_path: str) -> bool:
    try:
        raw = Path(yaml_path).read_text()
        data = yaml.safe_load(raw)
        LandscapeFile.model_validate(data)
        print(f"✓ {yaml_path} is valid")
        return True
    except ValidationError as e:
        print(f"✗ Validation failed:\n{e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"✗ Error reading {yaml_path}: {e}", file=sys.stderr)
        return False


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "data/landscape.yaml"
    sys.exit(0 if validate(path) else 1)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd agent && pytest tests/test_validate.py -v
```

Expected: 3 tests pass.

- [ ] **Step 5: Create the CI workflow**

```yaml
# .github/workflows/ci.yml
name: CI

on:
  pull_request:
    branches: [main]

jobs:
  validate-yaml:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"
      - run: pip install pydantic PyYAML
      - run: python agent/validate.py data/landscape.yaml
```

- [ ] **Step 6: Commit**

```bash
git add agent/validate.py agent/tests/test_validate.py .github/
git commit -m "feat: add YAML validation script and CI workflow"
```

---

## Phase 2: MCP Server

### Task 4: MCP Project Scaffold

**Files:**
- Create: `mcp/package.json`
- Create: `mcp/tsconfig.json`

- [ ] **Step 1: Create package.json**

```json
{
  "name": "csa-ai-landscape-mcp",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "build": "tsc",
    "start": "node dist/server.js",
    "test": "vitest run",
    "dev": "tsc --watch"
  },
  "dependencies": {
    "@modelcontextprotocol/sdk": "^1.0.0",
    "js-yaml": "^4.1.0"
  },
  "devDependencies": {
    "@types/js-yaml": "^4.0.9",
    "@types/node": "^22.0.0",
    "typescript": "^5.6.0",
    "vitest": "^2.0.0"
  }
}
```

- [ ] **Step 2: Create tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "outDir": "dist",
    "rootDir": "src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true
  },
  "include": ["src/**/*"],
  "exclude": ["src/**/*.test.ts", "node_modules"]
}
```

- [ ] **Step 3: Install dependencies**

```bash
cd mcp && npm install
```

Expected: `node_modules/` created, no errors.

- [ ] **Step 4: Commit**

```bash
git add mcp/package.json mcp/tsconfig.json mcp/package-lock.json
git commit -m "feat: scaffold MCP server project"
```

---

### Task 5: MCP Landscape Utilities

**Files:**
- Create: `mcp/src/landscape.ts`
- Create: `mcp/src/landscape.test.ts`

- [ ] **Step 1: Write the failing tests**

```typescript
// mcp/src/landscape.test.ts
import { describe, it, expect, beforeAll } from "vitest";
import * as path from "path";
import { fileURLToPath } from "url";
import { loadLandscape, listEntries, searchEntries, getStats } from "./landscape.js";
import type { Landscape } from "./landscape.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const YAML_PATH = path.resolve(__dirname, "../../../data/landscape.yaml");

let landscape: Landscape;

beforeAll(() => {
  landscape = loadLandscape(YAML_PATH);
});

describe("loadLandscape", () => {
  it("loads categories", () => {
    expect(landscape.categories.length).toBeGreaterThan(0);
  });
  it("loads entries", () => {
    expect(landscape.entries.length).toBeGreaterThan(0);
  });
});

describe("listEntries", () => {
  it("returns all entries with no filters", () => {
    expect(listEntries(landscape, {}).length).toBe(landscape.entries.length);
  });
  it("filters by category", () => {
    const results = listEntries(landscape, { category: "agentic-harnesses" });
    results.forEach((e) => expect(e.category).toBe("agentic-harnesses"));
  });
  it("filters by pricing", () => {
    const results = listEntries(landscape, { pricing: "freemium" });
    results.forEach((e) => expect(e.pricing).toBe("freemium"));
  });
  it("filters by license", () => {
    const results = listEntries(landscape, { license: "MIT" });
    results.forEach((e) => expect(e.license).toBe("MIT"));
  });
  it("returns empty array when no match", () => {
    expect(listEntries(landscape, { category: "nonexistent" })).toHaveLength(0);
  });
});

describe("searchEntries", () => {
  it("finds entries by name substring", () => {
    const results = searchEntries(landscape, "Claude");
    expect(results.some((e) => e.name.includes("Claude"))).toBe(true);
  });
  it("returns empty for no match", () => {
    expect(searchEntries(landscape, "xyzzy_no_match_99999")).toHaveLength(0);
  });
  it("is case-insensitive", () => {
    const upper = searchEntries(landscape, "CLAUDE");
    const lower = searchEntries(landscape, "claude");
    expect(upper.length).toBe(lower.length);
  });
});

describe("getStats", () => {
  it("returns correct total", () => {
    expect(getStats(landscape).total_entries).toBe(landscape.entries.length);
  });
  it("includes per_category counts", () => {
    const stats = getStats(landscape);
    expect(typeof stats.per_category).toBe("object");
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd mcp && npm test
```

Expected: `Cannot find module './landscape.js'`

- [ ] **Step 3: Implement landscape.ts**

```typescript
// mcp/src/landscape.ts
import * as fs from "fs";
import * as yaml from "js-yaml";

export interface Subcategory {
  id: string;
  name: string;
}

export interface Category {
  id: string;
  name: string;
  subcategories?: Subcategory[];
}

export interface Entry {
  id: string;
  name: string;
  category: string;
  subcategory?: string;
  organization: string;
  description: string;
  logo?: string;
  website: string;
  github?: string;
  license: string;
  pricing: string;
  api_available?: boolean;
  tags?: string[];
  added: string;
  updated: string;
}

export interface Landscape {
  categories: Category[];
  entries: Entry[];
}

export function loadLandscape(yamlPath: string): Landscape {
  const content = fs.readFileSync(yamlPath, "utf8");
  return yaml.load(content) as Landscape;
}

export interface EntryFilters {
  category?: string;
  subcategory?: string;
  tags?: string[];
  pricing?: string;
  license?: string;
  api_available?: boolean;
}

export function listEntries(landscape: Landscape, filters: EntryFilters): Entry[] {
  return landscape.entries.filter((e) => {
    if (filters.category && e.category !== filters.category) return false;
    if (filters.subcategory && e.subcategory !== filters.subcategory) return false;
    if (filters.pricing && e.pricing !== filters.pricing) return false;
    if (filters.license && e.license !== filters.license) return false;
    if (filters.api_available !== undefined && e.api_available !== filters.api_available) return false;
    if (filters.tags?.length) {
      const entryTags = e.tags ?? [];
      if (!filters.tags.every((t) => entryTags.includes(t))) return false;
    }
    return true;
  });
}

export function searchEntries(landscape: Landscape, query: string): Entry[] {
  const q = query.toLowerCase();
  return landscape.entries.filter(
    (e) =>
      e.name.toLowerCase().includes(q) ||
      e.description.toLowerCase().includes(q) ||
      e.organization.toLowerCase().includes(q) ||
      (e.tags ?? []).some((t) => t.toLowerCase().includes(q))
  );
}

export function getStats(landscape: Landscape) {
  const per_category: Record<string, number> = {};
  for (const cat of landscape.categories) {
    per_category[cat.id] = landscape.entries.filter((e) => e.category === cat.id).length;
  }
  const last_updated =
    landscape.entries
      .map((e) => e.updated)
      .sort()
      .reverse()[0] ?? null;
  return { total_entries: landscape.entries.length, per_category, last_updated };
}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd mcp && npm test
```

Expected: All tests pass.

- [ ] **Step 5: Commit**

```bash
git add mcp/src/landscape.ts mcp/src/landscape.test.ts
git commit -m "feat: add MCP landscape data utilities with tests"
```

---

### Task 6: MCP Server Entry Point

**Files:**
- Create: `mcp/src/server.ts`

- [ ] **Step 1: Implement server.ts**

```typescript
// mcp/src/server.ts
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import * as path from "path";
import { fileURLToPath } from "url";
import {
  loadLandscape,
  listEntries,
  searchEntries,
  getStats,
} from "./landscape.js";
import type { EntryFilters } from "./landscape.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const YAML_PATH =
  process.env.LANDSCAPE_YAML ??
  path.resolve(__dirname, "../../data/landscape.yaml");

const landscape = loadLandscape(YAML_PATH);

const server = new Server(
  { name: "csa-ai-landscape", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "list_categories",
      description: "List all landscape categories with entry counts",
      inputSchema: { type: "object" as const, properties: {} },
    },
    {
      name: "list_entries",
      description:
        "List entries with optional filters. All parameters are optional.",
      inputSchema: {
        type: "object" as const,
        properties: {
          category: { type: "string", description: "Category ID" },
          subcategory: { type: "string", description: "Subcategory ID" },
          tags: { type: "array", items: { type: "string" }, description: "All tags must match" },
          pricing: { type: "string", enum: ["free", "freemium", "paid", "enterprise"] },
          license: { type: "string", description: "SPDX identifier or 'proprietary'" },
          api_available: { type: "boolean" },
        },
      },
    },
    {
      name: "get_entry",
      description: "Get full details for a single entry by ID",
      inputSchema: {
        type: "object" as const,
        properties: { id: { type: "string" } },
        required: ["id"],
      },
    },
    {
      name: "search_entries",
      description: "Full-text search across name, description, organization, and tags",
      inputSchema: {
        type: "object" as const,
        properties: { query: { type: "string" } },
        required: ["query"],
      },
    },
    {
      name: "get_stats",
      description: "Total entry count per category and last-updated date",
      inputSchema: { type: "object" as const, properties: {} },
    },
  ],
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  const a = (args ?? {}) as Record<string, unknown>;

  switch (name) {
    case "list_categories": {
      const stats = getStats(landscape);
      return {
        content: [
          {
            type: "text" as const,
            text: JSON.stringify(
              landscape.categories.map((cat) => ({
                id: cat.id,
                name: cat.name,
                entry_count: stats.per_category[cat.id] ?? 0,
              })),
              null,
              2
            ),
          },
        ],
      };
    }

    case "list_entries": {
      const filters: EntryFilters = {
        category: a.category as string | undefined,
        subcategory: a.subcategory as string | undefined,
        tags: a.tags as string[] | undefined,
        pricing: a.pricing as string | undefined,
        license: a.license as string | undefined,
        api_available: a.api_available as boolean | undefined,
      };
      const entries = listEntries(landscape, filters);
      return {
        content: [
          {
            type: "text" as const,
            text: JSON.stringify(
              entries.map((e) => ({
                id: e.id,
                name: e.name,
                description: e.description,
                category: e.category,
                organization: e.organization,
                tags: e.tags,
              })),
              null,
              2
            ),
          },
        ],
      };
    }

    case "get_entry": {
      const entry = landscape.entries.find((e) => e.id === a.id);
      if (!entry) throw new Error(`Entry '${a.id}' not found`);
      return { content: [{ type: "text" as const, text: JSON.stringify(entry, null, 2) }] };
    }

    case "search_entries": {
      if (!a.query) throw new Error("query is required");
      const results = searchEntries(landscape, a.query as string);
      return {
        content: [
          {
            type: "text" as const,
            text: JSON.stringify(
              results.map((e) => ({
                id: e.id,
                name: e.name,
                description: e.description,
                category: e.category,
                tags: e.tags,
              })),
              null,
              2
            ),
          },
        ],
      };
    }

    case "get_stats":
      return { content: [{ type: "text" as const, text: JSON.stringify(getStats(landscape), null, 2) }] };

    default:
      throw new Error(`Unknown tool: ${name}`);
  }
});

const transport = new StdioServerTransport();
await server.connect(transport);
```

- [ ] **Step 2: Build to verify TypeScript compiles**

```bash
cd mcp && npm run build
```

Expected: `dist/server.js` and `dist/landscape.js` created, no TypeScript errors.

- [ ] **Step 3: Smoke-test the server**

```bash
cd mcp && echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | LANDSCAPE_YAML=../data/landscape.yaml node dist/server.js
```

Expected: JSON response listing 5 tools.

- [ ] **Step 4: Commit**

```bash
git add mcp/src/server.ts
git commit -m "feat: add MCP server with 5 read-only landscape tools"
```

---

### Task 7: MCP Dockerfile

**Files:**
- Create: `mcp/Dockerfile`

- [ ] **Step 1: Create Dockerfile (build from repo root)**

```dockerfile
# mcp/Dockerfile
FROM node:22-alpine AS builder
WORKDIR /app
COPY mcp/package*.json ./
RUN npm ci
COPY mcp/src/ src/
COPY mcp/tsconfig.json ./
RUN npx tsc

FROM node:22-alpine
WORKDIR /app
COPY --from=builder /app/dist/ dist/
COPY --from=builder /app/node_modules/ node_modules/
COPY data/landscape.yaml data/landscape.yaml
ENV LANDSCAPE_YAML=/app/data/landscape.yaml
EXPOSE 3000
CMD ["node", "dist/server.js"]
```

- [ ] **Step 2: Build the Docker image (from repo root)**

```bash
docker build -f mcp/Dockerfile -t csa-ai-landscape-mcp .
```

Expected: Image builds successfully.

- [ ] **Step 3: Commit**

```bash
git add mcp/Dockerfile
git commit -m "feat: add MCP server Dockerfile"
```

---

## Phase 3: Web Frontend

### Task 8: Astro Project Scaffold

**Files:**
- Create: `web/package.json`
- Create: `web/astro.config.mjs`
- Create: `web/public/.gitkeep`

- [ ] **Step 1: Create package.json**

```json
{
  "name": "csa-ai-landscape-web",
  "type": "module",
  "scripts": {
    "dev": "astro dev",
    "build": "astro build && npx pagefind --site dist",
    "preview": "astro preview"
  },
  "dependencies": {
    "astro": "^4.0.0",
    "js-yaml": "^4.1.0"
  },
  "devDependencies": {
    "@types/js-yaml": "^4.0.9",
    "pagefind": "^1.0.0"
  }
}
```

- [ ] **Step 2: Create astro.config.mjs**

```javascript
// web/astro.config.mjs
import { defineConfig } from "astro/config";

export default defineConfig({
  output: "static",
});
```

- [ ] **Step 3: Create public directories**

```bash
mkdir -p web/public/logos && touch web/public/logos/.gitkeep
```

Logos referenced in `landscape.yaml` (e.g. `logo: logos/claude.svg`) are served from `web/public/logos/`. Drop SVG files there as entries are added.

- [ ] **Step 4: Install dependencies**

```bash
cd web && npm install
```

Expected: `node_modules/` created, no errors.

- [ ] **Step 5: Commit**

```bash
git add web/
git commit -m "feat: scaffold Astro web frontend"
```

---

### Task 9: Astro Components

**Files:**
- Create: `web/src/components/EntryTile.astro`
- Create: `web/src/components/LandscapeGrid.astro`
- Create: `web/src/components/FilterBar.astro`

- [ ] **Step 1: Create EntryTile.astro**

```astro
---
// web/src/components/EntryTile.astro
interface Entry {
  id: string;
  name: string;
  description: string;
  website: string;
  logo?: string;
  organization: string;
  pricing: string;
  license: string;
  api_available?: boolean;
  tags?: string[];
  added: string;
}

interface Props {
  entry: Entry;
}

const { entry } = Astro.props;
const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)
  .toISOString()
  .split("T")[0];
const isNew = entry.added > thirtyDaysAgo;
---

<a
  href={entry.website}
  target="_blank"
  rel="noopener noreferrer"
  class="entry-tile"
  data-pagefind-body
  title={`${entry.name} — ${entry.description} (${entry.organization})`}
>
  {
    entry.logo ? (
      <img
        src={`/logos/${entry.logo}`}
        alt={entry.name}
        class="logo"
        width="20"
        height="20"
      />
    ) : (
      <div class="logo-placeholder">{entry.name[0]}</div>
    )
  }
  <span class="name">{entry.name}</span>
  {isNew && <span class="new-badge">NEW</span>}
</a>

<style>
  .entry-tile {
    display: flex;
    align-items: center;
    gap: 5px;
    padding: 5px 8px;
    background: #0f1a2a;
    border: 1px solid #1a2a3a;
    border-radius: 4px;
    text-decoration: none;
    color: #ccc;
    font-size: 11px;
    transition: border-color 0.15s, background 0.15s;
    max-width: 160px;
  }
  .entry-tile:hover {
    border-color: #2a4a6a;
    color: #fff;
    background: #111f30;
  }
  .logo {
    width: 20px;
    height: 20px;
    object-fit: contain;
    flex-shrink: 0;
  }
  .logo-placeholder {
    width: 20px;
    height: 20px;
    background: #1e3a5f;
    border-radius: 3px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 10px;
    font-weight: bold;
    color: #7eb8f7;
    flex-shrink: 0;
  }
  .name {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .new-badge {
    font-size: 8px;
    background: #1a3d2b;
    color: #6fcc8c;
    padding: 1px 4px;
    border-radius: 2px;
    flex-shrink: 0;
  }
</style>
```

- [ ] **Step 2: Create LandscapeGrid.astro**

```astro
---
// web/src/components/LandscapeGrid.astro
import EntryTile from "./EntryTile.astro";

interface Entry {
  id: string;
  name: string;
  category: string;
  description: string;
  website: string;
  logo?: string;
  organization: string;
  pricing: string;
  license: string;
  api_available?: boolean;
  tags?: string[];
  added: string;
}

interface Category {
  id: string;
  name: string;
}

interface Props {
  landscape: { categories: Category[]; entries: Entry[] };
}

const { landscape } = Astro.props;

const byCategory = Object.fromEntries(
  landscape.categories.map((cat) => [
    cat.id,
    landscape.entries.filter((e) => e.category === cat.id),
  ])
);
---

<main class="landscape">
  {
    landscape.categories.map((cat) => (
      <section class="category-section" data-category={cat.id}>
        <h2 class="category-header">
          {cat.name}
          <span class="count">{byCategory[cat.id]?.length ?? 0}</span>
        </h2>
        <div class="tile-grid">
          {(byCategory[cat.id] ?? []).map((entry) => (
            <EntryTile entry={entry} />
          ))}
        </div>
      </section>
    ))
  }
</main>

<style>
  .landscape {
    padding: 16px 20px;
  }
  .category-section {
    margin-bottom: 24px;
  }
  .category-header {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: #7eb8f7;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .count {
    font-size: 10px;
    background: #1e3a5f;
    color: #7eb8f7;
    padding: 2px 6px;
    border-radius: 10px;
    font-weight: normal;
    letter-spacing: 0;
  }
  .tile-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
  }
</style>
```

- [ ] **Step 3: Create FilterBar.astro**

```astro
---
// web/src/components/FilterBar.astro
interface Category {
  id: string;
  name: string;
}

interface Props {
  categories: Category[];
}

const { categories } = Astro.props;
---

<nav class="filter-bar">
  <button class="filter-btn active" data-category="all">All</button>
  {
    categories.map((cat) => (
      <button class="filter-btn" data-category={cat.id}>
        {cat.name}
      </button>
    ))
  }
</nav>

<style>
  .filter-bar {
    display: flex;
    gap: 4px;
    padding: 8px 20px;
    overflow-x: auto;
    background: #0d1520;
    border-bottom: 1px solid #1a2a3a;
    position: sticky;
    top: 52px;
    z-index: 9;
  }
  .filter-btn {
    padding: 4px 10px;
    border-radius: 4px;
    border: 1px solid #1a2a3a;
    background: transparent;
    color: #888;
    cursor: pointer;
    white-space: nowrap;
    font-size: 12px;
  }
  .filter-btn.active,
  .filter-btn:hover {
    background: #1e3a5f;
    color: #7eb8f7;
    border-color: #2a4a6a;
  }
</style>

<script>
  document.querySelectorAll(".filter-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document
        .querySelectorAll(".filter-btn")
        .forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      const cat = btn.getAttribute("data-category");
      document.querySelectorAll(".category-section").forEach((section) => {
        const show =
          cat === "all" || section.getAttribute("data-category") === cat;
        (section as HTMLElement).style.display = show ? "" : "none";
      });
    });
  });
</script>
```

- [ ] **Step 4: Commit**

```bash
git add web/src/
git commit -m "feat: add Astro landscape grid and filter components"
```

---

### Task 10: Astro Main Page

**Files:**
- Create: `web/src/pages/index.astro`

- [ ] **Step 1: Create index.astro**

```astro
---
// web/src/pages/index.astro
import yaml from "js-yaml";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import LandscapeGrid from "../components/LandscapeGrid.astro";
import FilterBar from "../components/FilterBar.astro";

const landscapePath = resolve(process.cwd(), "../data/landscape.yaml");
const landscape = yaml.load(readFileSync(landscapePath, "utf8")) as any;
---

<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>CSA AI Landscape</title>
    <meta
      name="description"
      content="A map of the AI ecosystem by the Cloud Security Alliance"
    />
    <style>
      *,
      *::before,
      *::after {
        box-sizing: border-box;
        margin: 0;
        padding: 0;
      }
      body {
        font-family: system-ui, -apple-system, sans-serif;
        background: #0a0f1a;
        color: #e0e0e0;
        min-height: 100vh;
      }
      header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 10px 20px;
        background: #0d1520;
        border-bottom: 1px solid #1a2a3a;
        position: sticky;
        top: 0;
        z-index: 10;
        height: 52px;
      }
      .site-title {
        font-size: 1rem;
        color: #7eb8f7;
        font-weight: 600;
      }
      .site-subtitle {
        font-size: 11px;
        color: #555;
        margin-left: 8px;
      }
      #search {
        width: 260px;
      }
    </style>
    <link rel="stylesheet" href="/pagefind/pagefind-ui.css" />
  </head>
  <body>
    <header>
      <div>
        <span class="site-title">CSA AI Landscape</span>
        <span class="site-subtitle"
          >{landscape.entries.length} tools across {landscape.categories.length} categories</span
        >
      </div>
      <div id="search"></div>
    </header>
    <FilterBar categories={landscape.categories} />
    <LandscapeGrid landscape={landscape} />
    <script src="/pagefind/pagefind-ui.js"></script>
    <script>
      // @ts-ignore
      new PagefindUI({ element: "#search", showSubResults: false });
    </script>
  </body>
</html>
```

- [ ] **Step 2: Build and verify**

```bash
cd web && npm run build
```

Expected: `dist/` directory created, `dist/index.html` exists, no build errors.

- [ ] **Step 3: Preview locally**

```bash
cd web && npm run preview
```

Open `http://localhost:4321`. Verify:
- Header shows entry count
- 12 category sections visible
- All 3 seed entries appear
- Filter buttons show/hide categories
- Search bar renders (index may be empty until Pagefind runs)

- [ ] **Step 4: Commit**

```bash
git add web/src/pages/
git commit -m "feat: add Astro main landscape page"
```

---

## Phase 4: Python Agent

### Task 11: Agent Research Module

**Files:**
- Create: `agent/requirements.txt`
- Create: `agent/research.py`
- Create: `agent/tests/test_research.py`

- [ ] **Step 1: Create requirements.txt**

```
anthropic>=0.40.0
pydantic>=2.0.0
PyYAML>=6.0
PyGitHub>=2.0.0
pytest>=8.0.0
```

- [ ] **Step 2: Write the failing test**

```python
# agent/tests/test_research.py
from unittest.mock import MagicMock, patch
from research import parse_agent_response, strip_code_fences


def test_strip_code_fences_json_block():
    raw = "```json\n[{\"id\": \"x\"}]\n```"
    assert strip_code_fences(raw) == '[{"id": "x"}]'


def test_strip_code_fences_plain():
    raw = '[{"id": "x"}]'
    assert strip_code_fences(raw) == '[{"id": "x"}]'


def test_parse_agent_response_valid():
    raw = '[{"id": "tool-a", "name": "Tool A", "category": "developer-tools", "organization": "Org", "description": "A dev tool", "website": "https://tool-a.com", "license": "MIT", "pricing": "free"}]'
    results = parse_agent_response(raw)
    assert len(results) == 1
    assert results[0]["id"] == "tool-a"


def test_parse_agent_response_invalid_json():
    results = parse_agent_response("this is not json")
    assert results == []


def test_parse_agent_response_not_a_list():
    results = parse_agent_response('{"id": "x"}')
    assert results == []
```

- [ ] **Step 3: Run to verify they fail**

```bash
cd agent && pip install -r requirements.txt && pytest tests/test_research.py -v
```

Expected: `ModuleNotFoundError: No module named 'research'`

- [ ] **Step 4: Implement research.py**

```python
# agent/research.py
import json
import anthropic
from schema import LandscapeFile
import yaml
from pathlib import Path


def strip_code_fences(text: str) -> str:
    """Remove markdown code fences from a string."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        # Remove first line (``` or ```json) and last line (```)
        inner = lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
        return "\n".join(inner).strip()
    return text


def parse_agent_response(raw: str) -> list[dict]:
    """Parse Claude's JSON response into a list of entry dicts. Returns [] on failure."""
    try:
        data = json.loads(strip_code_fences(raw))
        if not isinstance(data, list):
            return []
        return data
    except (json.JSONDecodeError, ValueError):
        return []


def load_existing(yaml_path: str) -> LandscapeFile:
    data = yaml.safe_load(Path(yaml_path).read_text())
    return LandscapeFile.model_validate(data)


def research_category(
    category_id: str,
    existing_ids: set[str],
    client: anthropic.Anthropic,
) -> list[dict]:
    """Ask Claude to find tools in category_id not already in the landscape."""
    skip = sorted(existing_ids)
    prompt = f"""You are a researcher building a landscape map of the AI ecosystem for the Cloud Security Alliance.

Research the category: **{category_id}**

Return a JSON array of notable tools/projects in this category. Each entry must have:
- id: unique kebab-case slug
- name: display name
- category: "{category_id}"
- organization: company or maintainer name
- description: 1-2 sentences, max 150 characters
- website: official URL (must start with https://)
- github: GitHub URL or null
- license: SPDX identifier (e.g. MIT, Apache-2.0, GPL-3.0) or "proprietary"
- pricing: one of "free", "freemium", "paid", "enterprise"
- api_available: true or false
- tags: list of up to 5 relevant tags

Skip these IDs (already in the landscape): {skip}

Return ONLY a valid JSON array. No prose, no markdown, no commentary."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    return parse_agent_response(response.content[0].text)
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd agent && pytest tests/test_research.py -v
```

Expected: 5 tests pass.

- [ ] **Step 6: Commit**

```bash
git add agent/requirements.txt agent/research.py agent/tests/test_research.py
git commit -m "feat: add agent research module with Claude API integration"
```

---

### Task 12: Agent GitHub PR Module

**Files:**
- Create: `agent/github_pr.py`
- Create: `agent/tests/test_github_pr.py`

- [ ] **Step 1: Write the failing test**

```python
# agent/tests/test_github_pr.py
from unittest.mock import MagicMock, patch, call
from github_pr import build_pr_body


def test_build_pr_body_lists_entries():
    entries = [
        {"name": "Tool A", "website": "https://a.com", "description": "Does A things"},
        {"name": "Tool B", "website": "https://b.com", "description": "Does B things"},
    ]
    body = build_pr_body("developer-tools", entries)
    assert "Tool A" in body
    assert "https://a.com" in body
    assert "2 entries" in body
    assert "developer-tools" in body
```

- [ ] **Step 2: Run to verify it fails**

```bash
cd agent && pytest tests/test_github_pr.py -v
```

Expected: `ModuleNotFoundError: No module named 'github_pr'`

- [ ] **Step 3: Implement github_pr.py**

```python
# agent/github_pr.py
import os
import yaml
from datetime import date, datetime
from pathlib import Path
from github import Github


def build_pr_body(category_id: str, entries: list[dict]) -> str:
    """Build the PR description body listing all new entries with source URLs."""
    lines = [
        f"Automated PR adding {len(entries)} entries to `{category_id}`.",
        "",
        "**New entries:**",
    ]
    for e in entries:
        lines.append(f"- [{e['name']}]({e['website']}) — {e['description']}")
    lines += [
        "",
        "_Review: verify each tool is real, correctly categorized, and the description is accurate._",
    ]
    return "\n".join(lines)


def open_pr(
    repo_name: str,
    category_id: str,
    new_entries: list[dict],
    yaml_path: str,
) -> str:
    """Append new_entries to landscape.yaml and open a GitHub PR. Returns PR URL."""
    g = Github(os.environ["GITHUB_TOKEN"])
    repo = g.get_repo(repo_name)

    data = yaml.safe_load(Path(yaml_path).read_text())
    today = date.today().isoformat()
    for entry in new_entries:
        entry["added"] = today
        entry["updated"] = today
    data["entries"].extend(new_entries)

    new_content = yaml.dump(
        data, default_flow_style=False, allow_unicode=True, sort_keys=False
    )

    branch = f"agent/add-{category_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    base = repo.get_branch("main")
    repo.create_git_ref(f"refs/heads/{branch}", base.commit.sha)

    contents = repo.get_contents("data/landscape.yaml", ref="main")
    repo.update_file(
        "data/landscape.yaml",
        f"agent: add {len(new_entries)} entries to {category_id}",
        new_content,
        contents.sha,  # type: ignore[union-attr]
        branch=branch,
    )

    pr = repo.create_pull(
        title=f"agent: add {len(new_entries)} entries to {category_id}",
        body=build_pr_body(category_id, new_entries),
        head=branch,
        base="main",
    )
    return pr.html_url
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd agent && pytest tests/test_github_pr.py -v
```

Expected: 1 test passes.

- [ ] **Step 5: Commit**

```bash
git add agent/github_pr.py agent/tests/test_github_pr.py
git commit -m "feat: add agent GitHub PR creation module"
```

---

### Task 13: Agent Orchestration Entry Point

**Files:**
- Create: `agent/agent.py`

- [ ] **Step 1: Implement agent.py**

```python
# agent/agent.py
#!/usr/bin/env python3
"""
CLI entry point for the landscape agent.

Usage:
  python agent.py --yaml data/landscape.yaml --repo org/repo
  python agent.py --category agentic-harnesses --dry-run
"""
import argparse
import os
import sys
import yaml
from pydantic import ValidationError
import anthropic

from schema import LandscapeEntry
from research import load_existing, research_category
from github_pr import open_pr
from validate import validate


def next_category(yaml_path: str, skip: list[str]) -> str | None:
    """Return the category with the oldest most-recently-updated entry."""
    landscape = load_existing(yaml_path)
    candidates = [c.id for c in landscape.categories if c.id not in skip]
    if not candidates:
        return None

    def oldest_update(cat_id: str) -> str:
        entries = [e for e in landscape.entries if e.category == cat_id]
        if not entries:
            return "0000-00-00"
        return max(str(e.updated) for e in entries)

    return min(candidates, key=oldest_update)


def run(
    category_id: str | None,
    yaml_path: str,
    repo: str,
    dry_run: bool,
) -> None:
    client = anthropic.Anthropic()
    landscape = load_existing(yaml_path)
    existing_ids = {e.id for e in landscape.entries}

    target = category_id or next_category(yaml_path, [])
    if not target:
        print("No categories to research.")
        return

    print(f"Researching: {target}")
    candidates = research_category(target, existing_ids, client)

    valid: list[dict] = []
    for raw in candidates:
        try:
            LandscapeEntry(**{**raw, "added": date.today().isoformat(), "updated": date.today().isoformat()})
            valid.append(raw)
        except ValidationError as e:
            print(f"  Skipping '{raw.get('id', '?')}': {e}", file=sys.stderr)

    if not valid:
        print("No valid entries found — nothing to PR.")
        return

    print(f"Found {len(valid)} valid entries.")

    if dry_run:
        print(yaml.dump({"new_entries": valid}, default_flow_style=False))
        return

    if not repo:
        print("--repo is required when not using --dry-run", file=sys.stderr)
        sys.exit(1)

    url = open_pr(repo, target, valid, yaml_path)
    print(f"PR opened: {url}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CSA AI Landscape agent")
    parser.add_argument("--category", help="Category ID to research (default: auto)")
    parser.add_argument("--yaml", default="data/landscape.yaml")
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""))
    parser.add_argument("--dry-run", action="store_true", help="Print instead of opening PR")
    args = parser.parse_args()
    run(args.category, args.yaml, args.repo, args.dry_run)
```

- [ ] **Step 2: Smoke-test with dry-run (requires ANTHROPIC_API_KEY)**

```bash
cd .. && ANTHROPIC_API_KEY=your_key python agent/agent.py \
  --category developer-tools \
  --yaml data/landscape.yaml \
  --dry-run
```

Expected: Prints YAML of proposed new entries, no PR opened.

- [ ] **Step 3: Commit**

```bash
git add agent/agent.py
git commit -m "feat: add agent orchestration entry point with dry-run mode"
```

---

## Phase 5: CI/CD

### Task 14: Deploy and Agent Workflows

**Files:**
- Create: `.github/workflows/deploy.yml`
- Create: `.github/workflows/agent.yml`

- [ ] **Step 1: Create deploy.yml**

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy-web:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: "22"

      - name: Install and build web
        run: cd web && npm ci && npm run build

      - name: Deploy to Cloudflare Pages
        uses: cloudflare/pages-action@v1
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
          projectName: csa-ai-landscape
          directory: web/dist

  deploy-mcp:
    runs-on: ubuntu-latest
    needs: deploy-web
    steps:
      - uses: actions/checkout@v4

      - name: Set up Fly.io
        uses: superfly/flyctl-actions/setup-flyctl@master

      - name: Build and deploy MCP container
        run: flyctl deploy --dockerfile mcp/Dockerfile --remote-only
        working-directory: mcp
        env:
          FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}
        # Requires a fly.toml in mcp/ — create with: cd mcp && flyctl launch --no-deploy
```

- [ ] **Step 2: Create agent.yml**

```yaml
# .github/workflows/agent.yml
name: Landscape Agent

on:
  schedule:
    - cron: "0 9 * * 1" # Every Monday at 9am UTC
  workflow_dispatch:
    inputs:
      category:
        description: "Category ID to research (leave blank for auto-select)"
        required: false
        default: ""

jobs:
  run-agent:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"

      - name: Install agent dependencies
        run: pip install -r agent/requirements.txt

      - name: Run agent (auto category)
        if: ${{ inputs.category == '' }}
        run: python agent/agent.py --yaml data/landscape.yaml --repo ${{ github.repository }}
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Run agent (specific category)
        if: ${{ inputs.category != '' }}
        run: python agent/agent.py --yaml data/landscape.yaml --repo ${{ github.repository }} --category ${{ inputs.category }}
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

- [ ] **Step 3: Document required GitHub secrets**

Add to `docs/system-design.md` under a new "Setup" section:

```markdown
## Required GitHub Secrets

| Secret | Purpose |
|--------|---------|
| `CLOUDFLARE_API_TOKEN` | Deploy web to Cloudflare Pages |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare account for Pages deployment |
| `FLY_API_TOKEN` | Deploy MCP server container to Fly.io |
| `ANTHROPIC_API_KEY` | Agent calls Claude API to research tools |
| `GITHUB_TOKEN` | Auto-provided by GitHub Actions — agent opens PRs |
```

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/deploy.yml .github/workflows/agent.yml docs/system-design.md
git commit -m "feat: add deploy and agent GitHub Actions workflows"
```

---

## Done

At this point the full system is implemented:

- ✅ `data/landscape.yaml` — validated YAML with 12 categories and seed entries
- ✅ `agent/` — Pydantic schema, validation CLI, research + PR agent
- ✅ `mcp/` — TypeScript MCP server with 5 read-only tools, Dockerized
- ✅ `web/` — Astro static site with dense grid, category filter, Pagefind search
- ✅ `.github/workflows/` — CI validation, deploy on merge, weekly agent cron

**Next steps after deployment:**
1. Set the 5 GitHub Secrets listed above
2. Create a Cloudflare Pages project named `csa-ai-landscape`
3. Create a Fly.io app for the MCP server (`flyctl launch` from `mcp/`)
4. Run the agent manually for the first time: `Actions → Landscape Agent → Run workflow`

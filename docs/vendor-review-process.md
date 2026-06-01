# Vendor Review Process

| Field | Value |
|---|---|
| **Status** | Draft |
| **Created** | 2026-06-01 |
| **Related** | `docs/rfc-001-vision.md`, `agent/schema.py`, `agent/propose.py`, `data/landscape.yaml` |

---

## 1. Purpose

The CSA AI Security Landscape is a vendor-neutral market map maintained by the Cloud Security Alliance. Every entry that appears in `data/landscape.yaml` — the single source of truth for the landscape — must be factually accurate, consistently structured, and free of promotional language.

This document defines the process by which entries are proposed, evaluated, and approved before reaching production. It covers:

- The conceptual review status model used to track entry maturity
- Principles that govern what may and may not appear in an entry
- The step-by-step workflow from proposal to merge
- A field-by-field guide for human reviewers
- How future review-assist agents should be designed
- A proposed review metadata model for future implementation
- Commands to validate data after edits

This process applies to all new entries and to any proposed changes to existing entries, regardless of whether the proposal originates from a human researcher, a vendor self-submission, or an automated agent.

**Scope boundaries.** Per RFC-001, this landscape is not a vendor review or rating platform, not a procurement recommendation tool, and does not rank vendors within categories. The review process exists to ensure entries are accurate and vendor-neutral — not to evaluate or endorse the vendors themselves.

---

## 2. Review Status Model

Entries move through four conceptual stages before and after reaching production. These stages are **policy terms defined here for human use** — they are not yet implemented as schema fields in `agent/schema.py` or `data/landscape.yaml`. See [Section 8](#8-future-review-metadata-model-not-implemented) for the proposed future schema.

### seed

Entries added to bootstrap the initial dataset without full source verification. The current entries in `data/landscape.yaml` are seed data, added to establish the taxonomy and demonstrate coverage. The file itself carries a prominent warning:

```
# NOTE: csa_member flags in this seed dataset are unverified sample data.
# All csa_member values must be confirmed against the CSA member roster
# before this data is used in production.
```

Seed entries require the same review pass as any proposed entry before being treated as verified production data.

### needs-review

Agent-generated proposals written to `agent/proposals/` by `agent/propose.py`, or human-drafted YAML blocks awaiting review. Entries at this stage have not been checked against primary sources and **must not be copied into `data/landscape.yaml` without completing the review workflow in Section 5.**

### reviewed

A human reviewer has checked all fields against primary sources (vendor website, public documentation, GitHub repository, CSA member roster as applicable) and corrected or removed unsupported claims. The entry is ready for PR review.

### verified

All claims are confirmed, including `csa_member` status validated against the CSA member roster. The entry has passed schema validation and PR review and is eligible for merge to `main`.

---

## 3. Why Agents Assist But Do Not Approve

Agents in this project — including `agent/propose.py` and any future enrichment or verification agents — generate proposals and surface information to support human decision-making. They do not approve entries, and no agent output may be merged to `data/landscape.yaml` without explicit human review and PR approval.

**Why this constraint exists:**

- Agents work from public sources and may encounter stale, inaccurate, or promotional content. Claims that read as factual on a vendor website may be aspirational or no longer accurate.
- Language models can hallucinate plausible-sounding details — integration names, pricing tiers, license identifiers — that have no basis in fact.
- The `csa_member` field cannot be verified from public web sources alone; it requires checking against the CSA member roster, which agents do not have reliable access to.
- The landscape is a CSA-published resource. Errors that reach production carry reputational weight for the organization.

RFC-001 defines four human intervention points in the agentic pipeline: taxonomy policy approval, submission and edit approval, edge case adjudication, and quality audits. The review process here corresponds to the second intervention point.

**What agents may do:**

- Generate template proposals for human completion
- Populate fields from public sources as a research starting point
- Flag fields where source evidence is missing or weak
- Suggest safer wording for claims that appear promotional or unverified
- Produce structured review notes for the human reviewer to evaluate

**What agents may not do:**

- Set `csa_member: true`
- Mark an entry as reviewed or verified
- Write directly to `data/landscape.yaml`
- Approve or merge a PR

The proposal header generated by `agent/propose.py` makes this explicit:

```
# Human review required before copying entries into data/landscape.yaml.
# 1. Verify all fields against the vendor's public documentation.
# 2. Verify csa_member against the CSA member roster before setting to true.
```

---

## 4. Review Principles

These principles govern all entries in the landscape, whether proposed by agents, human researchers, or vendors themselves.

### Vendor-neutral language

Descriptions must state what a product does, not how good it is. Superlatives, marketing language, and comparative claims are not permitted.

| Not permitted | Preferred |
|---|---|
| "industry-leading platform" | omit; describe capabilities instead |
| "best-in-class detection" | omit |
| "uniquely positioned to..." | omit |
| "comprehensive solution" | describe specific capabilities |

Write in the third person, present tense, using plain technical language.

### No rankings

Entries are not ranked within categories or across the landscape. The order in which entries appear in `data/landscape.yaml` does not imply ranking. No field in the schema encodes rank, score, or rating.

### No endorsements

The landscape describes what vendors offer. Inclusion in the landscape is not an endorsement by CSA. Entry descriptions must not be written in a way that could be read as a recommendation. Do not use language like "recommended for", "ideal for", or "the right choice for".

### No unverified CSA member claims

`csa_member` must remain `false` unless the reviewer has explicitly confirmed membership against the current CSA member roster. Setting `csa_member: true` on the basis of a vendor's self-reported claim, a website badge, or agent-generated output is not acceptable. When in doubt, leave it `false`.

### No speculative claims

Entries must describe current, verifiable capabilities. Do not include:

- Features announced but not yet generally available
- Capabilities described as "planned", "coming soon", or "in beta" without a stable release
- Partnerships or certifications that cannot be confirmed from primary sources
- Acquisition or ownership claims without a confirmed public announcement

### Cautious treatment of high-risk fields

Several fields are particularly prone to error or change:

| Field | Risk | Caution |
|---|---|---|
| `pricing` | Tiers change frequently; vendors often obscure pricing | Only use enum values from schema; when uncertain, use a more conservative tier or omit |
| `integrations` | Vendors list aspirational integrations; depth varies widely | Only list integrations with documented, current support |
| `license` | Open-source projects may use multiple licenses; components may differ | Use the SPDX identifier for the primary license; "proprietary" for commercial products without an open-source release |
| `csa_member` | Cannot be verified from public sources | Leave `false` unless confirmed against the CSA member roster |
| Acquisitions | Ownership changes; product names change after acquisition | Reflect current ownership and product name; note parent organization in `organization` field only if the product is marketed under the parent name |
| Product names | Vendors rebrand; product names split from company names | Use the name the vendor uses for the product at the time of review |

---

## 5. Review Workflow

### Step 1 — Proposed entry

An entry enters the review queue in one of three ways:

- **Agent proposal**: `agent/propose.py` writes a YAML block to `agent/proposals/`. The file is marked `# Status: PENDING REVIEW`.
- **Human draft**: A researcher writes a YAML block directly in `agent/proposals/` using the template format.
- **Vendor self-submission**: A vendor submits a product brief through the submission portal (post-MVP). The submission verification agent produces a discrepancy report; both the brief and the report are included in the review package.

### Step 2 — Source and evidence collection

Before touching the YAML, the reviewer should gather sources for the entry. Minimum sources:

- **Vendor website**: Confirm product name, description, and website URL.
- **Documentation or product pages**: Confirm integrations, API availability, and pricing tier.
- **GitHub repository** (if applicable): Confirm license identifier, activity, and open-source status.
- **CSA member roster**: Required if `csa_member` is `true` or being considered.
- **Press or funding announcements** (if applicable): Confirm organization name, acquisition status.

Sources should be documented in the PR description or in a future `evidence_urls` field (see Section 8).

### Step 3 — Human review

Review each field against the guidance in Section 6. Correct or remove any field value that cannot be supported by a primary source. Apply the principles in Section 4.

If a field value is genuinely uncertain after source review, prefer the conservative option (e.g., `csa_member: false`, a more general pricing tier) over a guess.

### Step 4 — Schema validation

After editing, validate the full YAML file before opening a PR. See Section 9 for commands. Fix any validation errors before proceeding.

### Step 5 — PR review

Open a pull request targeting `main`. The PR description should include:

- Which entry or entries are being added or changed
- A brief summary of the sources reviewed
- Any fields where certainty is low and why

A second human reviewer reads the diff, checks that principles in Section 4 are met, and approves or requests changes.

### Step 6 — Merge

After PR approval, the entry is merged to `main` and the CI/CD pipeline deploys the updated landscape. The entry is now in the **verified** state.

---

## 6. Field Reviewer Guide

All valid field values are defined in `agent/schema.py`. Reference that file as the authoritative source for enumerations.

### `name`

The product name as the vendor uses it publicly. Use the current name — not a prior name, internal codename, or informal abbreviation. If a product has been renamed after an acquisition, use the current marketed name.

### `organization`

The company or open-source maintainer that publishes the product. For commercial products, this is typically the company legal name or the name used in press and marketing. For open-source tools maintained by a larger organization (e.g., NVIDIA maintaining Garak), use the maintainer organization name. Do not add "Inc.", "Ltd.", or similar suffixes unless the vendor consistently uses them in product branding.

### `category`

Must be a valid category `id` from the `categories` block of `data/landscape.yaml`. Confirm that the primary category reflects the vendor's core offering, not a secondary capability. If the fit is ambiguous, use `capability_tags` for secondary categories rather than forcing a primary assignment.

### `description`

One to two sentences describing what the product does. Apply vendor-neutral language (Section 4). Check that:

- No superlatives or marketing claims are present
- The description reflects current product capabilities
- The language is accurate to the primary category — not a general company description
- It is written at the product level, not the company level

Aim for the same register as: "Real-time prompt injection and jailbreak detection for LLM applications, deployable as an API gateway to inspect inputs and outputs before they reach or leave the model."

### `website`

The canonical product URL. Prefer a product-specific URL over a homepage when one exists (e.g., `https://crowdstrike.com/products/identity-protection` rather than `https://crowdstrike.com`). Confirm the URL resolves.

### `license`

Use the [SPDX identifier](https://spdx.org/licenses/) for open-source licenses (e.g., `Apache-2.0`, `MIT`). Use `proprietary` for commercial products without a public open-source release. Do not use informal terms like "open source", "freeware", or "commercial". If a project uses multiple licenses across components, use the license that governs the primary distributed artifact.

### `pricing`

Must be one of the four enum values defined in `schema.py`:

| Value | Meaning |
|---|---|
| `free` | No cost, no paid tier |
| `freemium` | Free tier available; paid tiers exist |
| `paid` | Paid product; no meaningful free tier |
| `enterprise` | Pricing by contract; no public pricing |

When a vendor does not publish pricing, default to `enterprise`. Do not guess based on company size or market segment.

### `api_available`

`true` if the vendor provides a documented, programmatic API for integrating with the product — not just a UI. Confirm from documentation; do not infer from the product category.

### `vendor_type`

Must be one of:

| Value | Meaning |
|---|---|
| `ai-native` | Core product is built around AI capabilities; AI is not an add-on |
| `cloud-native` | Cloud-first platform that has added AI features |
| `hybrid` | Spans both — significant pre-AI history with substantial AI capability |

This classification helps buyers understand whether AI is central to the product or an enhancement to an existing platform. When in doubt, lean toward `hybrid` rather than forcing a classification.

### `csa_member`

**Default: `false`. Only set to `true` after confirming against the current CSA member roster.**

This field must not be set based on:
- A badge or claim on the vendor's website
- Agent-generated output
- A prior reviewer's assertion without a documented check

When reviewing seed entries or agent proposals, treat this field as unconfirmed until explicitly verified.

### `tags`

Free-form capability keywords describing the product's features and market vocabulary. Tags support search and filtering. Guidelines:

- Use lowercase kebab-case (e.g., `prompt-injection`, `model-scanning`)
- Include terms buyers and practitioners are likely to search
- Do not duplicate the primary category id or include terms that don't apply
- Aim for 3–6 meaningful tags; avoid tag inflation

### `capability_tags`

Category IDs from the landscape taxonomy that describe secondary or ancillary capabilities. A vendor whose primary category is `prompt-defense` but that also addresses `agent-security` should list `agent-security` in `capability_tags`. Must be valid category IDs — validate against the `categories` block.

### `buyer_problems`

A list of plain-language problems this vendor's product addresses. Written from the buyer's perspective, not the vendor's. Guidelines:

- Each item should be a specific, actionable problem a practitioner faces
- Avoid vague entries like "improve security posture" — be concrete
- Do not use marketing language or vendor-provided copy verbatim
- 3–5 items is typical; more than 6 usually indicates scope inflation

### `integrations`

The platforms and ecosystems the product integrates with. Only include integrations that are documented and currently supported — not roadmap or aspirational integrations. Common integration names should match the format used in the existing entries (e.g., `AWS`, `Azure`, `GCP`, `CrowdStrike`, `Splunk`, `Okta`) for consistency.

### `maestro_layers`

One or more MAESTRO layer identifiers indicating where in the AI stack this vendor operates. Valid values are defined in `schema.py`:

| Identifier | Layer |
|---|---|
| `L1-foundation-models` | Foundation models and base model capabilities |
| `L2-data-operations` | Data pipelines, training data, vector stores |
| `L3-agent-frameworks` | Agent frameworks, orchestration, tool use |
| `L4-deployment-infrastructure` | Inference infrastructure, serving, compute |
| `L5-observability-feedback` | Monitoring, tracing, evaluation, feedback |
| `L6-security-controls` | Security enforcement, guardrails, access control |
| `L7-ecosystem-governance` | Policy, compliance, governance, risk management |

Assign layers that reflect where the product operates, not aspirational coverage. Unknown values are hard errors in schema validation.

### `aicm_control_families`

One or more AICM control family identifiers mapping the vendor to the CSA AI Controls Matrix. Valid values:

| Identifier | Family |
|---|---|
| `GRM` | Governance & Risk Management |
| `CAI` | Compliance & AI Assurance |
| `IAM` | Identity & Access Management |
| `DSP` | Data Security & Privacy |
| `TP` | Threat Protection |
| `INS` | Infrastructure Security |
| `IRS` | Incident Response |
| `SC` | Supply Chain Security |

Assign families that the product directly addresses. Do not assign broadly to increase apparent coverage. Unknown values are hard errors in schema validation.

---

## 7. Future Review-Assist Agents

As the landscape scales, automated agents will be introduced to support human reviewers without replacing them. This section defines how those agents should behave.

### What review-assist agents should do

**Generate structured review notes.** For each field in a proposed entry, the agent should produce a note indicating what source was consulted and whether the field value appears to match that source. Review notes are inputs to the human reviewer — not determinations.

**Flag unsupported claims.** When a field value cannot be corroborated from available sources, the agent should flag it with a reason. Examples: a pricing tier that contradicts published pricing pages, an integration listed on the vendor's site as "coming soon", a `csa_member: true` value with no roster confirmation.

**Suggest safer wording.** When description language appears promotional or unverifiable, the agent should offer a neutral rewrite as a suggestion. The human reviewer decides whether to accept it.

**Identify missing evidence.** If an integration, license, or capability claim lacks a cited source, the agent should surface that gap rather than silently accepting the value.

### What review-assist agents must not do

- Set `csa_member: true`
- Write a `review_status` of `reviewed` or `verified` without human confirmation
- Write entries directly to `data/landscape.yaml`
- Approve or comment on pull requests as an approving authority
- Resolve flagged issues autonomously

### Design principle

Review-assist agents produce **advisory outputs** consumed by a human reviewer. Their output format should make it easy for the reviewer to confirm or override each judgment — not require the reviewer to re-derive the conclusion from scratch. The agent's role is to do the research legwork; the reviewer's role is to make the final call.

---

## 8. Future Review Metadata Model (Not Implemented)

The current schema (`agent/schema.py`) and `data/landscape.yaml` do not include review status or provenance fields. This section documents a proposed extension for future implementation. **Nothing in this section is currently active.**

### Proposed fields

```yaml
# Proposed additions to LandscapeEntry — not yet in schema.py

review_status: seed          # seed | needs-review | reviewed | verified
reviewed_by: null            # GitHub username or email of reviewer
review_date: null            # ISO 8601 date of most recent review
evidence_urls: []            # Source URLs consulted during review
```

### Intent

| Field | Purpose |
|---|---|
| `review_status` | Machine-readable stage; enables filtering for audit and tooling |
| `reviewed_by` | Accountability trail; identifies who last verified the entry |
| `review_date` | Freshness signal; entries older than a threshold can be flagged for re-review |
| `evidence_urls` | Source documentation; supports reproducibility and dispute resolution |

### Why deferred

Adding these fields requires a schema migration, updates to the validator, MCP server, and web frontend. The review process can be followed as a human workflow without schema changes. These fields will be added when the tooling to consume them is ready.

---

## 9. Validation Commands

After any edit to `data/landscape.yaml`, run all three checks before opening a pull request. Fix any errors before proceeding.

**Validate the YAML schema:**

```bash
cd agent && python3 validate.py ../data/landscape.yaml
```

Checks that all entries conform to the Pydantic models in `schema.py`, including valid category IDs, valid MAESTRO layer identifiers, valid AICM control family identifiers, unique entry IDs, and required field types.

**Run the test suite:**

```bash
cd agent && python3 -m pytest tests/ -v
```

Runs all agent-layer tests. Must pass with no failures before opening a PR.

**Build the web frontend:**

```bash
cd web && npm run build
```

Confirms the Astro site builds successfully against the updated YAML. A build failure indicates a data issue that affects the web layer even if schema validation passed.

All three checks must pass before a PR is opened. CI runs the same checks on every PR automatically.

# Agentic AI Security Innovator Market Map — Gap Analysis

**Source:** Cloud Security Alliance, "Agentic AI Security Innovator Market Map," May 2026
**Audit date:** 2026-06-24
**Branch:** feature/agentic-ai-market-map-sync
**Auditor:** Claude Code (automated audit + human review required)

---

## 1. Executive Summary

The CSA Agentic AI Security Innovator Market Map (May 2026) lists **22 unique companies** across five capability categories: Identity, Governance, Observability, Supply Chain Integrity, and Vendor-Neutral Guardrails.

Cross-referencing these 22 companies against the AI Landscape dataset (`data/landscape.yaml`) finds:

- **1 exact match** — Astrix Security already has a canonical record (`astrix-security`).
- **0 alias/variation matches** — No records resolved via alias or name variation.
- **0 probable matches requiring confirmation** — No close-but-uncertain matches found.
- **21 companies missing** from the dataset.

**Website sourcing:** The CSA market-map PDF contains embedded hyperlinks for all 22 companies. These links are the source for all 22 `website` values; a CSA-provided hyperlink records where the PDF points, but does not confirm company identity — the Security Consultant OÜ case (§9, item 1) shows that a CSA-linked URL can resolve to an unrelated platform. All 22 website values in the dataset are CSA-sourced; `website` has been removed from `verification_needed` on all new entries. A correction pass updated 16 entries where agent-inferred domains differed from the CSA-linked destinations (see §5.3).

This document drives the synchronization work on `feature/agentic-ai-market-map-sync`. Phase 3 adds all 21 missing companies as minimal `needs-review` entries and enriches the existing Astrix Security record with market-map capability tags.

---

## 2. Match Summary

| Classification | Count |
|---|---|
| Exact match | 1 |
| Alias / variation match | 0 |
| Probable match (needs human confirmation) | 0 |
| Missing from dataset | 21 |
| **Total** | **22** |

---

## 3. Company-by-Company Comparison Table

> Market-map categories: **I** = Identity, **G** = Governance, **O** = Observability, **SC** = Supply Chain Integrity, **VNG** = Vendor-Neutral Guardrails

| # | Source name | Existing canonical name | Slug | Match class | Existing primary category | Market-map categories | Action |
|---|---|---|---|---|---|---|---|
| 1 | Adversa AI | — | — | Missing | — | G, O | Added |
| 2 | Aembit | — | — | Missing | — | I, G, SC | Added |
| 3 | Aiceberg | — | — | Missing | — | G, O, VNG | Added |
| 4 | Akto | — | — | Missing | — | I, G, O, SC, VNG | Added |
| 5 | ArgusEye | — | — | Missing | — | I, G, O, SC | Added |
| 6 | Astrix Security | Astrix Security | astrix-security | **Exact match** | agent-security | I, G, O, SC, VNG | Market-map tags added |
| 7 | Daylight Security | — | — | Missing | — | I | Added |
| 8 | Entro Security | — | — | Missing | — | I, G, O | Added |
| 9 | Harmonic | — | — | Missing | — | G, O, VNG | Added |
| 10 | Knostic | — | — | Missing | — | G, O, SC | Added |
| 11 | Permiso Security | — | — | Missing | — | I, O, SC | Added |
| 12 | Security Consultant OÜ | — | — | Missing | — | G | Added |
| 13 | Silmaril | — | — | Missing | — | VNG | Added |
| 14 | Skyhawk Security | — | — | Missing | — | I, O | Added |
| 15 | Straiker | — | — | Missing | — | G, O, SC, VNG | Added |
| 16 | Surepath AI | — | — | Missing | — | G, O, VNG | Added |
| 17 | Surf AI | — | — | Missing | — | I, G, O | Added |
| 18 | Tenet Security | — | — | Missing | — | G, O, VNG | Added |
| 19 | Terra Security | — | — | Missing | — | O | Added |
| 20 | The Cyber Bear Group | — | — | Missing | — | I, G, O, SC, VNG | Added |
| 21 | Token Security | — | — | Missing | — | I, G, O, SC, VNG | Added |
| 22 | Vorlon | — | — | Missing | — | I, G, O, SC, VNG | Added |

---

## 4. Duplicate and Alias Concerns

No suspected duplicates or alias collisions were identified. The search covered:

- Exact name comparison (case-insensitive).
- Partial name matching against `name`, `organization`, and free-text fields.
- Common suffixes (`Security`, `AI`, `Labs`, `Inc`).

**Harmonic** — the market-map company is **Harmonic Security** (harmonic.security), distinct from Harmonic Inc. (a video streaming technology company). No existing entry references Harmonic in either context. No collision risk.

**Token Security** — not to be confused with "token" in the cryptographic or API-key sense. This is a distinct NHI/secrets management vendor. No existing entry matches.

**The Cyber Bear Group** — the CSA-linked canonical domain is `grizzlycbg.io` (not `thecyberbeargroup.com`). "Grizzly CBG" = Cyber Bear Group. This link between display name and domain is noted in the entry's `review.notes`. No collision with other entries.

---

## 5. Additions and Updates

### 5.1 Update — Astrix Security (existing record)

**Slug:** `astrix-security`
**Website corrected:** `https://astrix.security` → `https://www.astrix.security` (CSA PDF source)
**Additional changes:** Market-map capability tags added to `tags` list; `updated` date and `review.notes` updated.
**Tags added:** `market-map-identity`, `market-map-governance`, `market-map-observability`, `market-map-supply-chain-integrity`, `market-map-vendor-neutral-guardrails`, `csa-agentic-ai-market-map-2026`

No other fields changed. Existing description, integrations, MAESTRO layers, and AICM families are preserved.

### 5.2 Additions — 21 new entries

All new entries follow these conventions:
- `review.status: needs-review` — nothing is verified or production-ready.
- `csa_member: false` — appearance on the market map does not confer membership status.
- Market-map provenance captured in `tags` via `csa-agentic-ai-market-map-2026` plus per-category tags.
- `buyer_problems`, `integrations` left empty — no reliable source available.
- `vendor_type`, `maestro_layers`, `aicm_control_families` are defensible inferences from company name and market-map context; all flagged for human review.
- `pricing` defaults to `enterprise` as consistent with the agentic AI security market; flagged for review.
- **`website` sourced from the CSA PDF** for all 22 entries and removed from `verification_needed`. A CSA-provided hyperlink is not the same as a confirmed company identity; see Security Consultant OÜ (§9, item 1), where the linked site resolves to an unrelated platform.

**CSA-provided canonical websites (authoritative):**

| Company | CSA-linked website | Slug |
|---|---|---|
| Adversa AI | https://adversa.ai | adversa-ai |
| Aembit | https://aembit.io/ | aembit |
| Aiceberg | https://aiceberg.ai/ | aiceberg |
| Akto | https://www.akto.io/ | akto |
| ArgusEye | https://arguseye.ai | arguseye |
| Astrix Security | https://www.astrix.security | astrix-security |
| Daylight Security | https://daylight.ai/ | daylight-security |
| Entro Security | https://entro.security | entro-security |
| Harmonic | https://www.harmonic.security/ | harmonic-security |
| Knostic | https://knostic.ai | knostic |
| Permiso Security | https://permiso.io | permiso-security |
| Security Consultant OÜ | https://www.securityconsultant.com | security-consultant-ou |
| Silmaril | https://silmaril.dev | silmaril |
| Skyhawk Security | https://www.skyhawk.security | skyhawk-security |
| Straiker | https://www.straiker.ai/ | straiker |
| Surepath AI | https://www.surepath.ai/ | surepath-ai |
| Surf AI | https://surf.ai | surf-ai |
| Tenet Security | https://www.tenetsecurity.ai | tenet-security |
| Terra Security | https://terra.security | terra-security |
| The Cyber Bear Group | https://grizzlycbg.io | the-cyber-bear-group |
| Token Security | https://www.token.security/ | token-security |
| Vorlon | https://vorlon.io | vorlon |

### 5.3 URL Correction Pass

After the initial gap analysis added 21 new entries using agent-inferred domains, a second pass replaced every website field with the CSA-embedded hyperlink. The following entries had domains that differed from the CSA-linked destination and were corrected:

| Entry | Agent-inferred (wrong) | CSA-provided (correct) | Nature of difference |
|---|---|---|---|
| astrix-security | https://astrix.security | https://www.astrix.security | www prefix added |
| aembit | https://aembit.io | https://aembit.io/ | trailing slash added |
| aiceberg | https://aiceberg.io | https://aiceberg.ai/ | TLD changed (.io → .ai) |
| akto | https://akto.io | https://www.akto.io/ | www prefix + trailing slash |
| arguseye | https://arguseye.com | https://arguseye.ai | TLD changed (.com → .ai) |
| daylight-security | https://daylightsec.com | https://daylight.ai/ | domain changed entirely |
| harmonic-security | https://harmonic.security | https://www.harmonic.security/ | www prefix + trailing slash |
| security-consultant-ou | https://securityconsultant.ee | https://www.securityconsultant.com | country TLD changed (.ee → .com) |
| silmaril | https://silmaril.ai | https://silmaril.dev | TLD changed (.ai → .dev) |
| skyhawk-security | https://skyhawksecurity.io | https://www.skyhawk.security | domain restructured |
| straiker | https://straiker.io | https://www.straiker.ai/ | TLD changed (.io → .ai) |
| surepath-ai | https://surepath.ai | https://www.surepath.ai/ | www prefix + trailing slash |
| tenet-security | https://tenetsecurity.com | https://www.tenetsecurity.ai | TLD changed (.com → .ai) |
| the-cyber-bear-group | https://thecyberbeargroup.com | https://grizzlycbg.io | domain changed entirely (brand name differs) |
| token-security | https://token.security | https://www.token.security/ | www prefix + trailing slash |
| vorlon | https://vorlon.security | https://vorlon.io | TLD changed (.security → .io) |

Entries with no URL change: `adversa-ai`, `entro-security`, `knostic`, `permiso-security`, `surf-ai`, `terra-security`.

**Metadata impact of corrected identities:**
The corrected URLs are consistent with the company identities described for 20 of the 21 new entries. The exception is Security Consultant OÜ: the CSA-linked site appears to be an unrelated platform and the company identity remains unconfirmed (see §9, item 1). For the other 20 entries, no description, organization name, primary category, tag, or capability tag required revision as a result of the URL corrections. The initial metadata was based on the company name and market-map context (not the guessed domain content), so it remained valid. Entries where the CSA-linked domain differs substantially from the display name have a note in `review.notes` (specifically, The Cyber Bear Group / grizzlycbg.io).

---

## 6. Taxonomy and Schema Concerns

### 6.1 Market-map categories are not primary categories

The five market-map headings (Identity, Governance, Observability, Supply Chain Integrity, Vendor-Neutral Guardrails) do **not** map cleanly to existing primary categories:

| Market-map category | Closest existing primary category | Notes |
|---|---|---|
| Identity | `agent-security` / `ai-identity` | The market-map Identity category focuses on non-human identities and AI agent credentials, which spans both existing categories. |
| Governance | `ai-governance` | Close mapping; existing category is broader (includes responsible AI, model registries). |
| Observability | `ai-observability` | Close mapping; market-map Observability has a stronger security focus than the existing category. |
| Supply Chain Integrity | `ai-supply-chain` | Near-direct mapping. |
| Vendor-Neutral Guardrails | `prompt-defense` | Partial mapping; guardrails include both prompt-level and policy-level controls beyond just prompt injection defense. |

**Decision:** No new primary categories were added. The market-map classifications are encoded as free-form tags (`market-map-identity`, `market-map-governance`, etc.) in the `tags` field, following the existing free-form tagging convention. This preserves the source classification information while avoiding a schema redesign.

**Proposed future taxonomy change (not implemented here):**
If the landscape evolves to include a dedicated "Agentic AI Security" area, the five market-map categories would be strong candidates for subcategories under that area. That change requires explicit design approval and updated schema validation.

### 6.2 Source provenance — no dedicated field

The schema has no dedicated `source` or `provenance` field. Source attribution is stored in `tags` (via `csa-agentic-ai-market-map-2026`) and in `review.notes`. If a provenance field is added in a future schema extension, these entries should be migrated.

### 6.3 CSA membership

**12 market-map organizations confirmed as CSA Members** by the project owner on 2026-06-24. Their records now use `csa_member: true`:

| # | Organization | Slug |
|---|---|---|
| 1 | Adversa AI | adversa-ai |
| 2 | Aembit | aembit |
| 3 | Akto | akto |
| 4 | ArgusEye | arguseye |
| 5 | Astrix Security | astrix-security |
| 6 | Entro Security | entro-security |
| 7 | Harmonic | harmonic-security |
| 8 | Silmaril | silmaril |
| 9 | Skyhawk Security | skyhawk-security |
| 10 | Straiker | straiker |
| 11 | Surepath AI | surepath-ai |
| 12 | Token Security | token-security |

The `csa_member` field for the remaining newly added organizations (Aiceberg, Daylight Security, Knostic, Permiso Security, Security Consultant OÜ, Surf AI, Tenet Security, Terra Security, The Cyber Bear Group, Vorlon) remains `false` — membership is unverified because the authoritative full CSA membership roster is not yet available for cross-reference.

Appearance on a CSA publication is not treated as evidence of CSA membership per project policy. `csa_member: false` records unverified status, not confirmed non-membership.

---

## 7. Validation Results

### 7.1 Schema validation

```
cd agent && python3 validate.py ../data/landscape.yaml
```

Result: `✓ ../data/landscape.yaml is valid`

### 7.2 Test suite

```
cd agent && python3 -m pytest tests/ -q
```

Result: `156 passed in 0.54s` — all tests pass, no failures.

### 7.3 Astro build

```
cd web && npm run build
```

Result: `1 page(s) built in 648ms` — build succeeded with no errors or warnings.

### 7.4 Uniqueness and integrity checks

- Total entries after sync: **69** (was 48 before this branch).
- Duplicate IDs: **none**.
- All 22 market-map companies resolve to exactly one canonical record: **confirmed**.
- Invalid category references: **none**.
- Invalid MAESTRO layer values: **none**.
- Invalid AICM family values: **none**.
- New entries with `csa_member: true`: **none** (correct — no membership inferred).
- Entries with guessed/wrong URLs remaining: **none** — all replaced by CSA-linked destinations.

### 7.5 Post-research validation

After enriching 20 of the 21 entries from official websites (Security Consultant OÜ remains unresolved — the CSA-linked site appears to be an unrelated platform; see §9, item 1):

```
cd agent && python3 validate.py ../data/landscape.yaml   # ✓ valid
cd agent && python3 -m pytest tests/ -q                  # 156 passed
cd web && npm run build                                   # ✓ 1 page built
```

All checks pass. Total entries: 69. Duplicate IDs: none.

---

## 8. Research Provenance Table

20 of the 21 new entries were enriched from their official websites; Security Consultant OÜ remains unresolved (see §9, item 1). CSA membership was not verified for any entry — an authoritative CSA membership roster was not available for cross-reference. `csa_member: false` records that membership status is unverified, not that a company is a confirmed non-member.

| # | Company | Website reviewed | Key pages | Primary capability | Desc changed | Category changed | Confidence | Remaining unverified fields |
|---|---|---|---|---|---|---|---|---|
| 1 | Adversa AI | adversa.ai | /platform, /blog | Continuous AI red teaming, 60+ vuln classes, MCP layer | Yes | No | High | api_available, pricing, csa_member |
| 2 | Aembit | aembit.io | /pricing, docs.aembit.io | Cloud-native NHI/workload IAM, secretless access | Yes | **Yes** (→ ai-identity) | High | csa_member |
| 3 | Aiceberg | aiceberg.ai | /pricing, /deployment | Real-time AI risk detection, 100+ signals, ICAP inline | Yes | **Yes** (→ ai-observability) | High | pricing, csa_member, Cranium AI acquisition status |
| 4 | Akto | akto.io | /pricing, /mcp-security, GitHub, docs | API + AI agent security, MIT OSS core, 1000+ probes | Yes | No | High | api_available, csa_member, OSS/commercial boundary |
| 5 | ArgusEye | arguseye.ai | /about, /blogs, /white-paper | Cyber-physical product security (OT/MedTech), NOT AI agent | Yes — completely | **Yes** (→ ai-vuln-management) | High | api_available, csa_member, GitHub (404) |
| 6 | Daylight Security | daylight.ai | /about, /blog | Managed Agentic Security Services (MDR), NOT AppSec/NHI | Yes — completely | **Yes** (→ ai-soc) | High | api_available, csa_member, full integration list |
| 7 | Entro Security | entro.security | /product, /integrations, /agentic-ai-security | NHI + agentic AI security, NHIDR engine, 60+ integrations | Yes | No | High | api_available, csa_member |
| 8 | Harmonic | harmonic.security | /pricing, /about, /blog | AI governance/DLP, intent-based classification, MCP gateway | Yes | **Yes** (→ ai-governance) | High | api_available, csa_member |
| 9 | Knostic | knostic.ai | /blog | AI coding safety, MCP security, shadow AI — shifted from LLM access control | Yes | **Yes** (→ agent-security) | Medium | api_available, csa_member, GitHub (404), pricing tier |
| 10 | Permiso Security | permiso.io | /product, /integrations, /ai-security, /about | Universal Identity Graph, ISPM + ITDR + AI agent runtime security | Yes | No | High | api_available, csa_member |
| 11 | Security Consultant OÜ | securityconsultant.com | /about, /pricing, /product, /services, /ai, /governance | **CRITICAL: wrong entity** — site is unrelated challenge-tracking tool | No | No | **Low — BLOCKER** | website (correct URL unknown), all fields |
| 12 | Silmaril | silmaril.dev | /docs, /status | Runtime AI application firewall, ModernBERT classifier, 20ms P90 | Yes | **Yes** (→ agent-security) | High | csa_member (claimed on site), pricing tier, GitHub |
| 13 | Skyhawk Security | skyhawk.security | /platform, /about, /resources, /ctem | Cloud purple team, digital twin adversarial simulation, CDR | Yes | **Yes** (→ ai-red-teaming) | High | api_available, csa_member |
| 14 | Straiker | straiker.ai | /product, /about, /blog | AI agent discovery + adversarial testing + runtime protection, 3 products | Yes | No | High | api_available, csa_member, GitHub |
| 15 | Surepath AI | surepath.ai + f5.com | /blog, /solutions, F5 product page | AI governance/DLP proxy (acquired by F5) | Yes | No | High | api_available, csa_member, F5 acquisition brand |
| 16 | Surf AI | surf.ai | /about, /blog | Agentic SecOps / automated posture remediation, NOT AI agent security | Yes — completely | **Yes** (→ ai-soc) | Medium | api_available, csa_member, integrations (limited) |
| 17 | Tenet Security | tenetsecurity.ai | /about, /product, /blog | Runtime AI agent security, agentjacking defense, Agent-Side Simulation | Yes | **Yes** (→ agent-security) | High | api_available, csa_member, GitHub |
| 18 | Terra Security | terra.security | /about, /product, /blog | Continuous automated pentesting platform — NOT AI observability/SPM | Yes — completely | **Yes** (→ ai-red-teaming) | High | api_available, csa_member |
| 19 | The Cyber Bear Group | grizzlycbg.io + cyberbeargroup.com | cyberbeargroup.com/why-choose-us | Asset intelligence + consulting (Grizzly platform) — NOT agentic AI security | Yes — completely | **Yes** (→ ai-observability) | Medium | csa_member, integrations, API docs (JS-rendered site) |
| 20 | Token Security | token.security | /product, /integrations, /blog | NHI + AI agent identity security, 1000+ integrations, RSA 2026 finalist | Yes | **Yes** (→ ai-identity) | High | csa_member, GitHub for OSS GCI tool |
| 21 | Vorlon | vorlon.io | /about, /blog, /platform | Agentic ecosystem security, DataMatrix engine, read-only API | Yes | No | High | csa_member, GitHub |

**Summary:** 13/21 categories changed. 5 descriptions were completely rewritten due to incorrect initial stubs (ArgusEye, Daylight Security, Surf AI, Terra Security, The Cyber Bear Group). 1 entry (Security Consultant OÜ) could not be enriched due to URL pointing to an unrelated company.

---

## 9. Remaining Ambiguities Requiring Human Review

1. **Security Consultant OÜ** — Research confirmed that `https://www.securityconsultant.com` is an unrelated challenge-tracking productivity platform with no AI security products. The correct website for the Estonian-registered Security Consultant OÜ entity is unknown. All metadata in this record is inferred only. A human reviewer must find and verify the correct URL before any production publication.

2. **Aiceberg** — Acquired by Cranium AI (noted on site). Verify whether Aiceberg operates as an independent product brand under Cranium AI, or whether the listing should be updated to reference Cranium AI instead.

3. **Surepath AI** — Acquired by F5. The surepath.ai domain and brand remain live but the core platform page redirects to f5.com. Verify whether this entry should be updated to reference F5 or maintained under the Surepath AI brand.

4. **The Cyber Bear Group** — The canonical domain `grizzlycbg.io` is a heavily JavaScript-rendered site. The product (Grizzly) and company (CBG) were researched from `cyberbeargroup.com`. Confirm the CSA PDF hyperlink maps to grizzlycbg.io and that both sites represent the same entity.

5. **ArgusEye** — Product is a cyber-physical/OT product security platform (not AI agent monitoring). The market-map categories (I, G, O, SC) may reflect a loose classification. Confirm with CSA whether this company was intentionally included in an agentic AI security map.

6. **CSA membership** — Not verified for any entry. `csa_member: false` throughout. Verify against the CSA member roster before any production publication. Silmaril claims CSA membership on its website.

7. **GitHub URLs** — Knostic (github.com/knostic-ai) and ArgusEye (github.com/arguseye) returned 404s during research. Confirm correct URLs if public repositories exist.

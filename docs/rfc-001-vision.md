# RFC-001: AI Security Landscape — Product Vision & Requirements

| Field | Value |
|---|---|
| **Status** | Draft |
| **Created** | 2026-05-21 |
| **Related** | `docs/system-design.md`, `docs/superpowers/specs/`, `docs/superpowers/plans/` |

---

## Summary

This document defines the product vision and requirements for the CSA AI Security Landscape — a vendor-neutral, continuously updated market map for AI security and observability. It differs from existing market maps (Gartner, Cyber Momentum, CNCF) through a multi-tag categorization model, CSA framework overlays (AICM control families and MAESTRO layers), natural language problem-to-solution search, and an integration ecosystem view.

---

## Motivation

The AI security and observability vendor landscape is expanding faster than existing market maps can represent it. Established formats force vendors into a single rigid category that rarely reflects their full capability scope, disadvantage startups whose products define new categories rather than fit existing ones, and give buyers an incomplete picture of how solutions stack together.

CSA's position as a vendor-neutral organization, combined with its framework ecosystem (AICM, MAESTRO), creates a unique opportunity to publish a market map that is practically useful to buyers while connecting to the broader CSA research body.

Three audiences drive the design:

- **Vendors** who need to accurately represent their capabilities and find their place in the ecosystem
- **Customers and practitioners** who need to navigate a complex landscape, evaluate fit, and understand how solutions compose into a technology stack
- **CSA** which benefits from highlighting member value, identifying prospective members, and surfacing market gaps relevant to its research agenda

---

## Goals

- Help vendors communicate how their capabilities fit the AI security and observability landscape
- Help customers navigate vendor options and understand how solutions stack into a technology stack
- Surface market gaps and unmet needs visible from landscape structure
- Overlay vendors onto AICM control families and MAESTRO layers, bringing CSA framework value directly to practitioners
- Highlight CSA members and support membership growth through visibility and prospective member identification
- Operate as a continuously updated living resource, not a periodic publication

---

## Non-Goals

- This is not a vendor review or rating platform
- This is not a replacement for CSA research publications
- This is not a procurement recommendation tool
- This project does not rank vendors within categories

---

## Coverage Scope

The landscape covers three overlapping areas:

### Security for AI
Capabilities that protect AI systems: model security, training pipeline integrity, agent and agentic workflow security, RAG system security, prompt injection defense, non-human identity (NHI) for agents, AI supply chain security, model evaluation and red-teaming.

### AI for Security
Capabilities that use AI to power security operations: AI-augmented SOC, AI-driven vulnerability management, AI-powered identity and access, AI threat intelligence, AI-assisted compliance.

### AI Observability, Governance, and Risk
Capabilities that provide visibility, control, and accountability over AI systems: AI observability and monitoring, AI governance platforms, AI risk management, model explainability, AI compliance tooling.

### Cross-Cutting Considerations

- Vendors are classified as **AI-native**, **cloud-native**, or **hybrid** to help customers avoid double-counting overlapping capabilities in adjacent categories
- Vendors operating across multiple frontier model providers (multi-AI environments) are distinguished from those tied to a single provider, helping customers understand portability and ecosystem lock-in
- Both startups and established vendors are included

---

## Key Features

### 1. Multi-Tag Categorization

Every vendor receives a **primary category** and one or more **ancillary tags**. Vendors are not forced to fit a single category. Tags reflect the full breadth of a vendor's capabilities, enabling:

- Vendors to accurately represent their scope without being misclassified
- Customers to find vendors from multiple capability angles
- The map to reveal which categories have dense coverage versus sparse coverage, helping: (market gap signal)
  - Customers identify duplication across their budget and security controls
  - Investors and innovators evaluate crowded markets versus high-need solution areas
  - CSA identify research priorities, event themes, and sponsorship opportunities among like companies and competitors


### 2. Problem-to-Category Natural Language Search

A free-text input where a customer describes a problem or requirement in plain language. A runtime agent returns the most relevant categories and highlights the vendors most likely to address the stated need. This removes the requirement to know category vocabulary before searching — customers can describe their problem and be guided to solutions.

### 3. Integration Ecosystem View

Each vendor profile includes the platforms and ecosystems it integrates with (AWS, Azure, GCP, Microsoft Sentinel, CrowdStrike, Splunk, Datadog, Okta, and others). A filterable view allows customers to explore by ecosystem, enabling stack composition and identifying integration gaps.

### 4. CSA Framework Overlay

Categories and vendors are mapped onto:

- **AICM control families** — practitioners can identify which vendors address specific AI Controls Matrix requirements
- **MAESTRO layers** — architects can understand where in the AI stack a vendor operates

This overlay is a primary differentiator and a direct connection between the market map and CSA's framework research.

### 5. CSA Member Highlighting

CSA member status is surfaced on vendor profiles throughout the public directory with 1 page briefing, links to their website, STAR registry when applicable. The internal research tool surfaces non-member vendors as prospective membership outreach candidates.

---

## Category Approach

Initial categories are derived from established, well-understood market maps rather than invented from scratch. Starting from recognized categories reduces adoption friction — practitioners already use this vocabulary.

Source taxonomies:
- Gartner Hype Cycle and Magic Quadrant categories
- Cyber Momentum AI security map
- CNCF AI/ML landscape
- Major VC firm AI security taxonomies

Adoption signal (how widely a category is recognized and used) weights inclusion in the initial taxonomy. Emergent tags capture capabilities not yet recognized as standalone categories.

All categories are then mapped to AICM control families and MAESTRO layers. This mapping is versioned and maintained as the taxonomy evolves over time.
Adoption signal (how widely a category is recognized and used) weights inclusion in 
the initial taxonomy. Emergent tags capture capabilities not yet recognized as 
standalone categories.

### Emerging Category Generation

The map also surfaces opportunities to define net-new categories before they are 
established by Gartner or other analysts, giving CSA a first-mover position in 
naming and framing new market segments. New categories can be proposed through two 
paths:

- **Vendor-driven** — vendors describing capabilities that don't fit existing 
categories signal an emerging space; patterns across multiple vendors in the same 
gap indicate a candidate category
- **Agent-driven** — the categorization agent flags clustering patterns in vendor 
capabilities that suggest an unnamed category, surfacing these to CSA for review 
and naming

CSA review and approval is required before any new category is published. This 
gives CSA the opportunity to align emerging categories with AICM and MAESTRO 
before they enter broader industry use.

All categories are then mapped to AICM control families and MAESTRO layers. This 
mapping is versioned and maintained as the taxonomy evolves over time.
---

## Vendor Submission and Self-Edit

### Initial Population
The discovery and enrichment agent pipeline populates the initial vendor set. Human researchers review a sampled ground truth set before public launch to calibrate agent accuracy.

### Vendor Self-Submission

- Vendors submit through a portal providing a structured form and a **1–2 page product brief**
- The submission verification agent independently scrapes the vendor's website and cross-checks all submitted claims, producing a discrepancy report
- A CSA reviewer sees the submission, the product brief, and the agent verification report before approving inclusion
- No vendor is added to the public directory without human approval

### Vendor Self-Edit

- Vendors may submit edits to their own profiles at any time
- All edits go through agent verification and CSA review before going live
- No changes are made to the source of truth without explicit approval

---

## Internal Research Tool

Visible to CSA staff only. Tracks per-vendor:

- Funding rounds and valuations
- CSA member status and membership tier
- Participation in CSA working groups
- Authorship in CSA research publications
- CSA research documents associated with the vendor's product category
- Enrichment freshness (last updated timestamp)

Surfaces a **prioritization view**: vendors that are not CSA members, are growing (funding signals), and operate in categories well-covered by CSA frameworks — flagged as high-priority outreach candidates.

---

## Agentic Architecture Overview

The landscape is maintained by a pipeline of specialized agents running continuously. Human involvement is limited to four defined intervention points:

1. **Taxonomy policy approval** — reviewing and approving proposed taxonomy changes
2. **Submission and edit approval** — reviewing agent-verified vendor submissions before they go live
3. **Edge case adjudication** — reviewing low-confidence categorizations flagged by the agent
4. **Quality audits** — sampled review of agent outputs to detect accuracy drift

### Pipeline Agents

| Agent | Responsibility |
|---|---|
| **Taxonomy Agent** | Synthesizes and versions the category taxonomy from source market maps; produces and maintains the AICM/MAESTRO mapping |
| **Discovery Agent** | Continuously sweeps sources (Crunchbase, conference exhibitor lists, VC portfolios, CSA member roster, funding announcements) for new vendor candidates |
| **Enrichment Agent** | Builds structured vendor profiles from websites, documentation, press, GitHub; classifies AI-native vs cloud-native vs hybrid |
| **Categorization Agent** | Assigns primary category and ancillary tags with confidence scores; flags low-confidence cases for human review |
| **Integration Graph Agent** | Extracts and verifies ecosystem integration claims against marketplace listings and vendor documentation |
| **CSA Intelligence Agent** | Cross-references vendors against member status, research authorship, working group participation, AICM/MAESTRO contribution history |
| **Funding & Status Agent** | Tracks funding rounds, valuations, acquisitions, leadership changes from news and data sources |
| **Submission Verification Agent** | Adversarially verifies vendor self-submissions — assumes submissions are optimistic, independently scrapes the vendor site, surfaces discrepancies for the human reviewer |

At runtime, a **problem-to-category search agent** handles natural language queries from the public directory search box.

---

## MVP Scope and Sequencing

| Milestone | Target | Deliverable |
|---|---|---|
| Week 1 end | Internal | Pipeline running end-to-end on 50+ vendors; taxonomy v1 mapped to AICM/MAESTRO |
| Week 2 end | Internal | 200+ vendors processed; basic HTML directory rendering; taxonomy frozen |
| Week 3 end | Public | Edge cases handled; internal soft-launch; public HTML MVP |

### Post-MVP Phases

- Vendor self-submission portal
- Problem-to-category natural language search
- Integration ecosystem view
- Internal CSA research tool
- Funding and status tracking
- AICM/MAESTRO framework overlay visualization

---

## Open Questions

1. **Frontier model providers** — do the providers themselves (Anthropic, OpenAI, Google, Meta) appear as vendors, or are they treated as infrastructure and ecosystem context only?

2. **Open source projects** — are open source security tools included? If so, what is the inclusion criterion (adoption threshold, commercial backing, active maintenance)?

3. **Cloud-native classification boundary** — what is the decision rule for distinguishing a "cloud-native security vendor with AI features" from an "AI-native security vendor"?

4. **Submission verification bar** — what confidence threshold does the verification agent need to reach before flagging for human review versus auto-approving? Recommendation: all submissions require human review at launch; loosen after calibration on the first cohort.

5. **Taxonomy governance** — who holds taxonomy change authority at CSA? Should working group leads have input into AICM/MAESTRO mapping decisions?

6. **Enrichment cadence** — how frequently should enrichment re-run per vendor? Recommendation: 30-day default cycle; 7-day for funding and status signals.

---

## Alternatives Considered

**Single-category model** — Existing market maps use rigid single-category placement. This forces vendors with multi-domain capabilities into a category that understates their scope and creates blind spots for buyers searching across categories. Rejected in favor of primary category plus tags.

**Building categories from scratch** — Inventing a novel taxonomy creates adoption friction with an audience that already uses Gartner and Cyber Momentum vocabulary. Starting from established categories and mapping them to AICM/MAESTRO preserves recognizability while adding CSA-specific value.

**Human-curated, batch-updated model** — A quarterly human-curated update cycle creates staleness, limits coverage, and cannot scale to the pace of the AI security market. The agent pipeline enables continuous updates and far broader coverage than a research team could maintain manually.

#!/usr/bin/env python3
"""
CSA AI Security Landscape — Local Proposal Agent

Generates proposed landscape entries for human review.
Proposals are written to agent/proposals/ and must be reviewed
before being copied into data/landscape.yaml.

Template mode (no API key required):
  python propose.py --template --category model-security
  python propose.py --template --problem "detect prompt injection on my LLM app"
  python propose.py --template --vendor "HiddenLayer"
  python propose.py --template --category model-security --dry-run

API mode (requires ANTHROPIC_API_KEY):
  python propose.py --category model-security
  python propose.py --problem "detect prompt injection on my LLM app"
  python propose.py --vendor "HiddenLayer"
"""
import argparse
import os
import re
import sys
from datetime import date
from pathlib import Path

import yaml
from pydantic import ValidationError

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from schema import LandscapeFile, MAESTRO_LAYERS, AICM_FAMILIES  # noqa: F401

DEFAULT_LANDSCAPE_YAML = Path(__file__).parent.parent / "data" / "landscape.yaml"
DEFAULT_PROPOSALS_DIR = Path(__file__).parent / "proposals"

# Keyword → category hints used for --problem and --vendor template mode
_PROBLEM_HINTS: list[tuple[list[str], str]] = [
    (["prompt inject", "jailbreak", "llm input", "llm output filter"], "prompt-defense"),
    (["agent security", "copilot", "non-human identity", "agentic workflow", "ai agent"], "agent-security"),
    (["model attack", "model theft", "adversarial ml", "model poison", "model backdoor", "model integrity"], "model-security"),
    (["supply chain", "model scan", "ai sbom", "model dependency", "model provenance"], "ai-supply-chain"),
    (["rag", "retrieval", "vector store", "data leak", "training data poison", "pii in ai", "sensitive data"], "rag-data-security"),
    (["red team", "redteam", "red-team", "vulnerability scan", "safety eval", "llm eval", "security test"], "ai-red-teaming"),
    (["soc", "threat detection", "detection and response", "edr", "xdr", "anomaly detection"], "ai-soc"),
    (["threat intel", "threat intelligence", "dark web", "ioc", "indicator of compromise"], "ai-threat-intel"),
    (["vulnerability management", "vuln", "patch priorit", "cve priorit"], "ai-vuln-management"),
    (["identity", "access management", "itdr", "lateral movement", "credential"], "ai-identity"),
    (["observabilit", "model monitor", "drift detect", "hallucination", "llm trac", "model performance"], "ai-observability"),
    (["governance", "model registry", "responsible ai", "model audit", "ai policy"], "ai-governance"),
    (["compliance", "ai risk", "regulation", "eu ai act", "nist ai", "iso 42001", "ai act"], "ai-risk-compliance"),
]


# ── Data loading ───────────────────────────────────────────────────────────────

def load_landscape(yaml_path: str | Path) -> LandscapeFile:
    """Load and validate the landscape YAML. Prints an error and exits on failure."""
    try:
        data = yaml.safe_load(Path(yaml_path).read_text())
        return LandscapeFile.model_validate(data)
    except ValidationError as e:
        print(f"✗ Landscape validation failed:\n{e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"✗ Could not load landscape: {e}", file=sys.stderr)
        sys.exit(1)


def validate_category(category_id: str, landscape: LandscapeFile) -> None:
    """Raise ValueError if category_id does not exist in the landscape."""
    valid_ids = {c.id for c in landscape.categories}
    if category_id not in valid_ids:
        raise ValueError(
            f"Unknown category '{category_id}'.\n"
            f"Valid categories: {', '.join(sorted(valid_ids))}"
        )


# ── Category suggestion ────────────────────────────────────────────────────────

def suggest_categories(problem: str, valid_category_ids: set[str]) -> list[str]:
    """Return category IDs whose keywords match the problem or vendor string.

    Returns at least one result: if no keywords match, falls back to the
    first three valid category IDs sorted alphabetically.
    """
    lower = problem.lower()
    matched: list[str] = []
    for keywords, cat_id in _PROBLEM_HINTS:
        if cat_id not in valid_category_ids:
            continue
        if any(kw in lower for kw in keywords):
            if cat_id not in matched:
                matched.append(cat_id)
    return matched or sorted(valid_category_ids)[:3]


# ── Path helpers ───────────────────────────────────────────────────────────────

def slugify(text: str, max_len: int = 40) -> str:
    """Convert text to a filename-safe kebab-case slug."""
    slug = re.sub(r"[^a-zA-Z0-9\s-]", "", text.lower())
    slug = re.sub(r"[\s-]+", "-", slug).strip("-")
    return slug[:max_len].rstrip("-")


def get_proposal_path(slug: str, proposals_dir: Path = DEFAULT_PROPOSALS_DIR) -> Path:
    """Return the output file path for a proposal."""
    today = date.today().isoformat()
    return proposals_dir / f"{today}-{slug}.yaml"


# ── Template generation ────────────────────────────────────────────────────────

def build_header(mode: str, target: str, extra_lines: list[str] | None = None) -> str:
    """Build the YAML header comment block for a proposal file."""
    today = date.today().isoformat()
    lines = [
        "# CSA AI Security Landscape — Proposal",
        f"# Generated: {today}",
        f"# Mode: {mode} — {target}",
        "# Status: PENDING REVIEW",
        "#",
        "# Human review required before copying entries into data/landscape.yaml.",
        "# 1. Verify all fields against the vendor's public documentation.",
        "# 2. Verify csa_member against the CSA member roster before setting to true.",
        "# 3. Validate: cd agent && python3 validate.py ../data/landscape.yaml",
        "# 4. Copy verified entries into data/landscape.yaml and open a PR for review.",
    ]
    if extra_lines:
        lines.append("#")
        lines.extend(f"# {line}" for line in extra_lines)
    return "\n".join(lines) + "\n"


def build_template_entry_yaml(category_id: str, name_hint: str = "") -> str:
    """Return a YAML sequence-element block for a template entry with field comments.

    The returned string starts with '  - ' and is suitable for inclusion under
    a 'proposals:' key. Inline and standalone comments are valid YAML and are
    ignored by parsers; they exist for human readers only.
    """
    today = date.today().isoformat()
    name_val = f'"{name_hint}"' if name_hint else '""'
    return (
        f'  - id: ""                    # unique kebab-case slug (e.g. vendor-name)\n'
        f"    name: {name_val}\n"
        f"    category: {category_id}\n"
        f'    organization: ""          # company or open-source maintainer name\n'
        f'    description: ""           # 1-2 sentences describing the product\n'
        f'    website: "https://"       # official website URL\n'
        f"    github: null              # GitHub URL or null\n"
        f'    license: proprietary      # SPDX identifier (MIT, Apache-2.0, etc.) or "proprietary"\n'
        f"    pricing: enterprise       # free | freemium | paid | enterprise\n"
        f"    api_available: false\n"
        f"    vendor_type: ai-native    # ai-native | cloud-native | hybrid\n"
        f"    csa_member: false         # MUST be verified against the CSA member roster\n"
        f"    tags: []\n"
        f"    capability_tags: []       # ancillary category IDs this vendor also addresses\n"
        f"    buyer_problems:           # plain-language problems this vendor solves\n"
        f'      - ""\n'
        f"    integrations: []          # e.g. [AWS, Azure, Splunk, CrowdStrike, Okta]\n"
        f"    maestro_layers: []\n"
        f"    # MAESTRO: L1-foundation-models  L2-data-operations  L3-agent-frameworks\n"
        f"    #          L4-deployment-infrastructure  L5-observability-feedback\n"
        f"    #          L6-security-controls  L7-ecosystem-governance\n"
        f"    aicm_control_families: []\n"
        f"    # AICM: GRM  CAI  IAM  DSP  TP  INS  IRS  SC\n"
        f"    added: {today}\n"
        f"    updated: {today}\n"
    )


def generate_template(
    mode: str,
    target: str,
    category_ids: list[str],
    name_hint: str = "",
    extra_header_lines: list[str] | None = None,
) -> str:
    """Generate a complete template proposal YAML string."""
    header = build_header(mode, target, extra_header_lines)
    entries = "\n".join(build_template_entry_yaml(cat, name_hint) for cat in category_ids)
    return header + "\nproposals:\n" + entries


def write_proposal(content: str, path: Path, dry_run: bool) -> None:
    """Write a proposal file, or print to stdout when dry_run is True."""
    if dry_run:
        print(content)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"✓ Proposal written to {path}")


def run_template(
    mode: str,
    target: str,
    landscape: LandscapeFile,
    dry_run: bool = False,
    proposals_dir: Path = DEFAULT_PROPOSALS_DIR,
) -> None:
    """Generate and output a template proposal (no API key required)."""
    valid_ids = {c.id for c in landscape.categories}

    if mode == "category":
        category_ids = [target]
        slug = target
        extra_lines: list[str] | None = None
        name_hint = ""

    elif mode == "problem":
        all_suggested = suggest_categories(target, valid_ids)
        category_ids = all_suggested[:1]
        slug = "problem-" + slugify(target, max_len=30)
        extra_lines = [
            f"Problem: {target}",
            f"Suggested categories: {', '.join(all_suggested)}",
            f"Template uses top match: {category_ids[0]}",
            "Adjust category: and add more proposals blocks for other matches.",
        ]
        name_hint = ""

    else:  # vendor
        all_suggested = suggest_categories(target, valid_ids)
        category_ids = all_suggested[:1]
        slug = slugify(target, max_len=40)
        extra_lines = [
            f"Vendor: {target}",
            f"Category is a best-effort suggestion — verify against the taxonomy.",
            f"All available categories: {', '.join(sorted(valid_ids))}",
        ]
        name_hint = target

    if not category_ids:
        print(f"✗ No matching category found for: {target!r}", file=sys.stderr)
        sys.exit(1)

    content = generate_template(
        mode, target, category_ids, name_hint=name_hint, extra_header_lines=extra_lines
    )
    path = get_proposal_path(slug, proposals_dir=proposals_dir)
    write_proposal(content, path, dry_run)


# ── API mode helpers (testable, lazy import of anthropic) ─────────────────────

def parse_api_response(raw: str) -> list[dict]:
    """Parse Claude's JSON response into a list of entry dicts.

    Strips markdown code fences if present. Returns [] on any parse failure.
    """
    import json

    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        end = next(
            (i for i in range(len(lines) - 1, 0, -1) if lines[i].strip() == "```"),
            len(lines),
        )
        text = "\n".join(lines[1:end]).strip()
    try:
        data = json.loads(text)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, ValueError):
        return []


def build_api_prompt(mode: str, target: str, landscape: LandscapeFile) -> str:
    """Build the Claude prompt for generating landscape entries."""
    today = date.today().isoformat()
    category_list = "\n".join(
        f"  - {c.id}: {c.name}" for c in landscape.categories
    )
    existing_ids = sorted(e.id for e in landscape.entries)

    if mode == "category":
        focus = f"Research vendors in category: **{target}**"
    elif mode == "problem":
        focus = (
            f"Customer problem to address: **{target}**\n"
            "Identify the most relevant categories and suggest vendors."
        )
    else:
        focus = f"Research the vendor: **{target}**"

    return (
        "You are a researcher building the CSA AI Security Landscape.\n\n"
        f"{focus}\n\n"
        "Available categories:\n"
        f"{category_list}\n\n"
        "Return a JSON array of proposed entries. Each entry MUST include:\n"
        "id, name, category, organization, description, website, github, license,\n"
        "pricing, api_available, vendor_type, csa_member, tags, capability_tags,\n"
        "buyer_problems, integrations, maestro_layers, aicm_control_families,\n"
        f'added ("{today}"), updated ("{today}")\n\n'
        "Rules:\n"
        "- id must be a unique kebab-case slug not in: "
        f"{existing_ids}\n"
        "- csa_member must always be false (human must verify)\n"
        "- maestro_layers values: L1-foundation-models, L2-data-operations,\n"
        "  L3-agent-frameworks, L4-deployment-infrastructure,\n"
        "  L5-observability-feedback, L6-security-controls, L7-ecosystem-governance\n"
        "- aicm_control_families values: GRM, CAI, IAM, DSP, TP, INS, IRS, SC\n\n"
        "Return ONLY a valid JSON array. No prose, no markdown, no code fences."
    )


def validate_api_entries(
    raw_entries: list[dict],
    landscape: LandscapeFile,
) -> tuple[list[dict], list[tuple[dict, str]]]:
    """Validate proposed entries against the schema.

    Returns (valid_entries, rejected_entries) where each rejection is
    a (raw_dict, reason_string) tuple.
    """
    from schema import LandscapeEntry

    existing_ids = {e.id for e in landscape.entries}
    valid: list[dict] = []
    rejected: list[tuple[dict, str]] = []

    for raw in raw_entries:
        entry_id = raw.get("id", "?")
        if entry_id in existing_ids:
            rejected.append((raw, f"ID '{entry_id}' already exists in landscape"))
            continue
        try:
            LandscapeEntry.model_validate(raw)
            valid.append(raw)
        except ValidationError as e:
            rejected.append((raw, str(e)))

    return valid, rejected


def run_api(
    mode: str,
    target: str,
    landscape: LandscapeFile,
    dry_run: bool = False,
    proposals_dir: Path = DEFAULT_PROPOSALS_DIR,
) -> None:
    """Call Claude to generate entries and write a proposal file."""
    try:
        import anthropic
    except ImportError:
        print("✗ anthropic package not installed. Run: pip install anthropic", file=sys.stderr)
        sys.exit(1)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print(
            "✗ ANTHROPIC_API_KEY is not set.\n"
            "  Use --template for template mode without an API key:\n"
            f"    python propose.py --template --{mode} {target!r}",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Calling Claude API ({mode}: {target!r}) ...")
    client = anthropic.Anthropic(api_key=api_key)
    prompt = build_api_prompt(mode, target, landscape)
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    raw_text = response.content[0].text
    raw_entries = parse_api_response(raw_text)

    if not raw_entries:
        print("✗ Claude returned no parseable entries.", file=sys.stderr)
        sys.exit(1)

    valid_entries, rejected = validate_api_entries(raw_entries, landscape)
    for raw, reason in rejected:
        print(f"  Skipping '{raw.get('id', '?')}': {reason}", file=sys.stderr)

    slug = slugify(target, max_len=40) if mode != "category" else target
    header = build_header(mode, target)

    if not valid_entries:
        content = header + "\nproposals: []\n# No valid entries were generated.\n"
    else:
        entries_yaml = yaml.dump(
            {"proposals": valid_entries},
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )
        content = header + "\n" + entries_yaml

    path = get_proposal_path(slug, proposals_dir=proposals_dir)
    write_proposal(content, path, dry_run)


# ── CLI entry point ────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="CSA AI Security Landscape — local proposal agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python propose.py --template --category model-security\n"
            "  python propose.py --template --problem 'detect prompt injection'\n"
            "  python propose.py --template --vendor 'HiddenLayer' --dry-run\n"
            "  python propose.py --category model-security   # requires ANTHROPIC_API_KEY"
        ),
    )

    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--category", metavar="CATEGORY_ID", help="Propose entries for a specific category")
    mode_group.add_argument("--problem", metavar="TEXT", help="Propose entries matching a plain-language problem")
    mode_group.add_argument("--vendor", metavar="NAME", help="Propose an entry for a specific vendor")

    parser.add_argument(
        "--template",
        action="store_true",
        help="Generate a template for manual completion (no API key required)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the proposal to stdout instead of writing a file",
    )
    parser.add_argument(
        "--landscape",
        default=str(DEFAULT_LANDSCAPE_YAML),
        metavar="PATH",
        help=f"Path to landscape.yaml (default: {DEFAULT_LANDSCAPE_YAML})",
    )

    args = parser.parse_args()

    landscape = load_landscape(args.landscape)

    # Determine mode and target
    if args.category:
        mode, target = "category", args.category
        try:
            validate_category(target, landscape)
        except ValueError as e:
            print(f"✗ {e}", file=sys.stderr)
            sys.exit(1)
    elif args.problem:
        mode, target = "problem", args.problem
    else:
        mode, target = "vendor", args.vendor

    # Choose template or API mode
    use_template = args.template or not os.environ.get("ANTHROPIC_API_KEY")

    if not args.template and not os.environ.get("ANTHROPIC_API_KEY"):
        print(
            "✗ ANTHROPIC_API_KEY is not set.\n"
            "  Use --template for template mode without an API key:\n"
            f"    python propose.py --template --{mode} {target!r}",
            file=sys.stderr,
        )
        sys.exit(1)

    if use_template:
        run_template(mode, target, landscape, dry_run=args.dry_run)
    else:
        run_api(mode, target, landscape, dry_run=args.dry_run)


if __name__ == "__main__":
    main()

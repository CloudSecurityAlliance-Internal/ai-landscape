#!/usr/bin/env python3
"""
CSA AI Security Landscape — Review-Assist Agent

Generates advisory Markdown review reports for landscape entries.
Reports are written to agent/reviews/ and are strictly read-only:
this agent never modifies data/landscape.yaml, never marks entries
reviewed or verified, never sets csa_member true, and makes no
external API calls.

Usage:
  python3 review.py --entry wiz --dry-run
  python3 review.py --status seed --dry-run
  python3 review.py --all --dry-run
  python3 review.py --entry wiz
  python3 review.py --all
"""
import argparse
import os
import sys
from datetime import date
from pathlib import Path

import yaml
from pydantic import ValidationError

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from schema import LandscapeEntry, LandscapeFile

DEFAULT_LANDSCAPE_YAML = Path(__file__).parent.parent / "data" / "landscape.yaml"
DEFAULT_REVIEWS_DIR = Path(__file__).parent / "reviews"

# ── Risky wording patterns ─────────────────────────────────────────────────────

RISKY_PATTERNS: list[str] = [
    "leading",
    "best",
    "dominant",
    "market-leading",
    "first",
    "only",
    "guaranteed",
    "proven",
    "complete",
    "fully",
]

# ── Per-field verification guidance ───────────────────────────────────────────

VERIFICATION_GUIDANCE: dict[str, str] = {
    "csa_member": (
        "Confirm against the current CSA member roster. "
        "Do not set to `true` based on vendor claims, website badges, or agent output."
    ),
    "pricing": (
        "Verify the current pricing tier on the vendor's pricing page. "
        "When pricing is not published, default to `enterprise`."
    ),
    "integrations": (
        "Confirm each listed integration is documented and currently supported. "
        "Do not include roadmap or aspirational integrations."
    ),
    "description": (
        "Review for promotional language, superlatives, and unverified claims. "
        "Descriptions should state what the product does, not how good it is."
    ),
    "license": (
        "Confirm the SPDX identifier from the repository or product documentation. "
        "Use `proprietary` for commercial products without a public open-source release."
    ),
    "vendor_type": (
        "Confirm whether AI is central to the product (`ai-native`) or an enhancement "
        "to an existing platform (`cloud-native` or `hybrid`). When in doubt, use `hybrid`."
    ),
    "maestro_layers": (
        "Verify layers reflect where the product currently operates, "
        "not aspirational coverage. Unknown layer identifiers fail schema validation."
    ),
    "aicm_control_families": (
        "Assign control families the product directly addresses. "
        "Do not assign broadly to increase apparent coverage."
    ),
    "api_available": (
        "Confirm from documentation that a programmatic API exists for integrating "
        "with the product — not just a UI."
    ),
    "github": (
        "Confirm the GitHub URL is current and points to the primary repository."
    ),
    "website": (
        "Confirm the URL resolves and is the current canonical product URL."
    ),
}

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


# ── Entry selection ────────────────────────────────────────────────────────────


def select_entries(
    landscape: LandscapeFile,
    entry_id: str | None = None,
    status: str | None = None,
) -> list[LandscapeEntry]:
    """Return matching entries. Raises ValueError if entry_id is given but not found."""
    if entry_id is not None:
        matches = [e for e in landscape.entries if e.id == entry_id]
        if not matches:
            raise ValueError(
                f"Entry '{entry_id}' not found in landscape.\n"
                f"Available IDs: {', '.join(sorted(e.id for e in landscape.entries))}"
            )
        return matches
    if status is not None:
        return [
            e for e in landscape.entries
            if e.review is not None and e.review.status == status
        ]
    return list(landscape.entries)


# ── Report path ────────────────────────────────────────────────────────────────


def get_report_path(entry_id: str, reviews_dir: Path = DEFAULT_REVIEWS_DIR) -> Path:
    """Return the deterministic output file path for a review report."""
    today = date.today().isoformat()
    return reviews_dir / f"{today}-{entry_id}.md"


# ── Wording analysis ───────────────────────────────────────────────────────────


def detect_risky_wording(entry: LandscapeEntry) -> list[dict]:
    """Scan description and buyer_problems for risky wording patterns.

    Returns a list of dicts with keys: field, term, text.
    Does not rewrite entries — findings are advisory only.
    """
    findings: list[dict] = []

    def _scan(field: str, text: str) -> None:
        lower = text.lower()
        for term in RISKY_PATTERNS:
            if term.lower() in lower:
                findings.append({"field": field, "term": term, "text": text})

    if entry.description:
        _scan("description", entry.description)

    for i, problem in enumerate(entry.buyer_problems):
        _scan(f"buyer_problems[{i}]", problem)

    return findings


# ── Report generation ──────────────────────────────────────────────────────────


def _fmt(value: object) -> str:
    """Format an optional value for display in a Markdown table."""
    if value is None:
        return "—"
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)


def build_report(entry: LandscapeEntry, today: str | None = None) -> str:
    """Build a Markdown review report for a single entry.

    The `today` parameter exists so tests can pass a fixed date.
    This function never writes files and never modifies the entry.
    """
    if today is None:
        today = date.today().isoformat()

    lines: list[str] = []

    # ── Header ─────────────────────────────────────────────────────────────────
    lines += [
        f"# Review Report: {entry.name} (`{entry.id}`)",
        "",
        f"> **Generated:** {today}  ",
        "> **Advisory only — this report does not modify `data/landscape.yaml`.**  ",
        "> **Humans must verify all findings and approve all changes before merging.**",
        "",
        "---",
        "",
    ]

    # ── Entry Details ──────────────────────────────────────────────────────────
    lines += [
        "## Entry Details",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| **ID** | `{entry.id}` |",
        f"| **Name** | {entry.name} |",
        f"| **Organization** | {entry.organization} |",
        f"| **Category** | `{entry.category}` |",
        f"| **Website** | {_fmt(entry.website)} |",
        f"| **License** | {entry.license} |",
        f"| **Pricing** | {entry.pricing} |",
        f"| **API Available** | {_fmt(entry.api_available)} |",
        f"| **Vendor Type** | {_fmt(entry.vendor_type)} |",
        f"| **CSA Member** | {_fmt(entry.csa_member)} |",
        "",
    ]

    # ── Review Metadata ────────────────────────────────────────────────────────
    lines += ["## Review Metadata", ""]
    if entry.review is None:
        lines += ["> No `review` block found.", ""]
    else:
        rev = entry.review
        lines += [
            "| Field | Value |",
            "|---|---|",
            f"| **Status** | `{rev.status}` |",
            f"| **Last Reviewed** | {_fmt(rev.last_reviewed)} |",
            f"| **Reviewed By** | {_fmt(rev.reviewed_by)} |",
            f"| **Notes** | {_fmt(rev.notes)} |",
            "",
        ]

    # ── Verification Needed ────────────────────────────────────────────────────
    if entry.review and entry.review.verification_needed:
        lines += [
            "## Verification Needed",
            "",
            "Fields flagged in the entry's `verification_needed` list:",
            "",
        ]
        for field in entry.review.verification_needed:
            guidance = VERIFICATION_GUIDANCE.get(
                field, "Verify field value against primary sources."
            )
            lines.append(f"- [ ] **`{field}`** — {guidance}")
        lines.append("")

    # ── Wording Checks ─────────────────────────────────────────────────────────
    risky = detect_risky_wording(entry)
    if risky:
        lines += [
            "## Potential Wording Issues",
            "",
            "The following terms may indicate promotional or unverifiable claims. "
            "Review each occurrence and rewrite to describe specific capabilities. "
            "This agent does not rewrite entries automatically.",
            "",
        ]
        for finding in risky:
            lines += [
                f"### `{finding['field']}` — term: **`{finding['term']}`**",
                "",
                f"> {finding['text'].strip()}",
                "",
                "**Safer wording guidance:** Describe what the product does, not how "
                "it compares to alternatives. Remove superlatives, comparative claims, "
                "and marketing language. Do not use terms like "
                f"`{finding['term']}` without a verifiable, neutral basis.",
                "",
            ]

    # ── Flags ──────────────────────────────────────────────────────────────────
    flag_blocks: list[str] = []

    if entry.review is None:
        flag_blocks.append(
            "### ⚠ Review metadata missing\n\n"
            "No `review` block found. Add a `review` block with `status`, "
            "`verification_needed`, and `notes` before publishing."
        )

    if entry.csa_member and (
        entry.review is None or entry.review.status != "verified"
    ):
        status_str = entry.review.status if entry.review else "none"
        flag_blocks.append(
            f"### ⚠ CSA member not verified\n\n"
            f"`csa_member` is `true` but review status is `{status_str}` "
            f"(not `verified`). Confirm against the current CSA member roster "
            "before publishing. Set to `false` if membership cannot be confirmed."
        )

    if not entry.website:
        flag_blocks.append(
            "### ⚠ Website missing\n\n"
            "`website` is empty or null. A canonical product URL is required."
        )

    if flag_blocks:
        lines += ["## Flags", ""]
        lines.append("\n\n---\n\n".join(flag_blocks))
        lines += ["", ""]

    # ── Reminders ──────────────────────────────────────────────────────────────
    lines += [
        "---",
        "",
        "## Reminders",
        "",
        "- This report is **advisory only**. No changes have been made to `data/landscape.yaml`.",
        "- A human reviewer must verify all flags and approve changes before merging.",
        "- To validate after edits: `cd agent && python3 validate.py ../data/landscape.yaml`",
        "- To run tests: `cd agent && python3 -m pytest tests/ -v`",
        "",
    ]

    return "\n".join(lines)


# ── File output ────────────────────────────────────────────────────────────────


def write_report(content: str, path: Path, dry_run: bool) -> None:
    """Write a report file, or print to stdout when dry_run is True."""
    if dry_run:
        print(content)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"✓ Report written to {path}")


def run_review(
    entries: list[LandscapeEntry],
    dry_run: bool = False,
    reviews_dir: Path = DEFAULT_REVIEWS_DIR,
) -> int:
    """Generate and output review reports for a list of entries.

    Returns the count of reports generated.
    """
    today = date.today().isoformat()
    separator = "\n" + ("─" * 72) + "\n"
    reports: list[str] = []

    for entry in entries:
        report = build_report(entry, today=today)
        path = get_report_path(entry.id, reviews_dir=reviews_dir)
        if dry_run:
            reports.append(report)
        else:
            write_report(report, path, dry_run=False)

    if dry_run and reports:
        print(separator.join(reports))

    return len(entries)


# ── CLI ────────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CSA AI Security Landscape — review-assist agent (report-only)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python3 review.py --entry wiz --dry-run\n"
            "  python3 review.py --status seed --dry-run\n"
            "  python3 review.py --entry wiz\n"
            "  python3 review.py --all --dry-run"
        ),
    )

    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--entry", metavar="ID", help="Review a single entry by ID")
    mode_group.add_argument(
        "--status",
        metavar="STATUS",
        choices=["seed", "needs-review", "reviewed", "verified"],
        help="Review all entries with the given review status",
    )
    mode_group.add_argument(
        "--all",
        action="store_true",
        help="Review all entries",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print reports to stdout instead of writing files",
    )
    parser.add_argument(
        "--landscape",
        default=str(DEFAULT_LANDSCAPE_YAML),
        metavar="PATH",
        help=f"Path to landscape.yaml (default: {DEFAULT_LANDSCAPE_YAML})",
    )

    args = parser.parse_args()
    landscape = load_landscape(args.landscape)

    if args.entry:
        try:
            entries = select_entries(landscape, entry_id=args.entry)
        except ValueError as e:
            print(f"✗ {e}", file=sys.stderr)
            sys.exit(1)
    elif args.status:
        entries = select_entries(landscape, status=args.status)
        if not entries:
            print(
                f"No entries with review status '{args.status}' found.",
                file=sys.stderr,
            )
            sys.exit(0)
    else:
        entries = select_entries(landscape)

    count = run_review(entries, dry_run=args.dry_run)
    noun = "report" if count == 1 else "reports"
    action = "Printed" if args.dry_run else "Generated"
    print(f"{action} {count} review {noun}.")


if __name__ == "__main__":
    main()

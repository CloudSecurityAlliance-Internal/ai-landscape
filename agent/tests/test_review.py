"""
Tests for agent/review.py — review-assist agent.

All tests use in-memory fixtures or tmp_path so no files
in agent/reviews/ are created or modified during the test run.
"""
import pytest
from datetime import date
from pathlib import Path

import yaml

from review import (
    DEFAULT_REVIEWS_DIR,
    build_report,
    detect_risky_wording,
    get_report_path,
    load_landscape,
    run_review,
    select_entries,
)
from schema import LandscapeEntry, LandscapeFile


# ── Fixtures ───────────────────────────────────────────────────────────────────

def _make_entry(**overrides) -> dict:
    """Return a valid entry dict with sensible defaults."""
    base: dict = {
        "id": "test-vendor",
        "name": "Test Vendor",
        "category": "model-security",
        "organization": "Test Corp",
        "description": "Detects adversarial attacks on ML models in production.",
        "website": "https://testvendor.example.com",
        "license": "proprietary",
        "pricing": "enterprise",
        "added": "2026-06-01",
        "updated": "2026-06-01",
        "review": {
            "status": "seed",
            "last_reviewed": None,
            "reviewed_by": None,
            "verification_needed": ["csa_member", "pricing", "integrations", "description"],
            "notes": "Seed entry. Requires human review.",
        },
    }
    return {**base, **overrides}


def _make_landscape(*extra_entries: dict) -> LandscapeFile:
    """Return a minimal LandscapeFile with a default entry plus any extras."""
    entries = [_make_entry()]
    entries.extend(extra_entries)
    return LandscapeFile.model_validate({
        "categories": [
            {"id": "model-security", "name": "Model Security", "area": "security-for-ai"},
            {"id": "prompt-defense", "name": "Prompt Defense", "area": "security-for-ai"},
        ],
        "entries": entries,
    })


def _entry(**overrides) -> LandscapeEntry:
    """Build a LandscapeEntry directly from the default dict."""
    return LandscapeEntry.model_validate({**_make_entry(), **overrides})


# ── load_landscape ─────────────────────────────────────────────────────────────

def test_load_landscape_real_yaml():
    yaml_path = Path(__file__).parents[2] / "data" / "landscape.yaml"
    landscape = load_landscape(yaml_path)
    assert isinstance(landscape, LandscapeFile)
    assert len(landscape.entries) > 0


def test_load_landscape_from_tmp_file(tmp_path):
    yaml_path = tmp_path / "test.yaml"
    data = {
        "categories": [{"id": "model-security", "name": "Model Security"}],
        "entries": [_make_entry()],
    }
    yaml_path.write_text(yaml.dump(data))
    landscape = load_landscape(yaml_path)
    assert len(landscape.entries) == 1
    assert landscape.entries[0].id == "test-vendor"


# ── select_entries ─────────────────────────────────────────────────────────────

def test_select_by_entry_id():
    landscape = _make_landscape(
        _make_entry(id="second-vendor", name="Second Vendor")
    )
    result = select_entries(landscape, entry_id="second-vendor")
    assert len(result) == 1
    assert result[0].id == "second-vendor"


def test_select_by_entry_id_not_found():
    landscape = _make_landscape()
    with pytest.raises(ValueError, match="not found"):
        select_entries(landscape, entry_id="does-not-exist")


def test_select_by_entry_id_error_lists_available_ids():
    landscape = _make_landscape()
    with pytest.raises(ValueError, match="test-vendor"):
        select_entries(landscape, entry_id="does-not-exist")


def test_select_by_status_seed():
    landscape = _make_landscape(
        _make_entry(
            id="verified-vendor",
            name="Verified Vendor",
            review={"status": "verified", "verification_needed": []},
        )
    )
    result = select_entries(landscape, status="seed")
    assert len(result) >= 1
    assert all(e.review is not None and e.review.status == "seed" for e in result)
    assert all(e.id != "verified-vendor" for e in result)


def test_select_by_status_verified():
    landscape = _make_landscape(
        _make_entry(
            id="verified-vendor",
            name="Verified Vendor",
            review={"status": "verified", "verification_needed": []},
        )
    )
    result = select_entries(landscape, status="verified")
    assert len(result) == 1
    assert result[0].id == "verified-vendor"


def test_select_by_status_returns_empty_for_no_match():
    landscape = _make_landscape()
    result = select_entries(landscape, status="verified")
    assert result == []


def test_select_all_returns_all_entries():
    landscape = _make_landscape(
        _make_entry(id="second-vendor", name="Second Vendor")
    )
    result = select_entries(landscape)
    assert len(result) == len(landscape.entries)


def test_select_excludes_entries_without_review_when_filtering_by_status():
    landscape = _make_landscape(
        _make_entry(id="no-review-vendor", name="No Review Vendor", review=None)
    )
    result = select_entries(landscape, status="seed")
    assert all(e.id != "no-review-vendor" for e in result)


# ── get_report_path ────────────────────────────────────────────────────────────

def test_report_path_is_under_reviews_dir(tmp_path):
    path = get_report_path("test-vendor", reviews_dir=tmp_path)
    assert path.parent == tmp_path


def test_report_path_contains_entry_id(tmp_path):
    path = get_report_path("wiz", reviews_dir=tmp_path)
    assert "wiz" in path.name


def test_report_path_contains_today(tmp_path):
    path = get_report_path("wiz", reviews_dir=tmp_path)
    assert date.today().isoformat() in path.name


def test_report_path_has_md_extension(tmp_path):
    path = get_report_path("wiz", reviews_dir=tmp_path)
    assert path.suffix == ".md"


def test_report_path_is_deterministic(tmp_path):
    path_a = get_report_path("wiz", reviews_dir=tmp_path)
    path_b = get_report_path("wiz", reviews_dir=tmp_path)
    assert path_a == path_b


def test_default_report_path_is_under_reviews_dir():
    path = get_report_path("wiz")
    assert path.parent == DEFAULT_REVIEWS_DIR


# ── detect_risky_wording ───────────────────────────────────────────────────────

def test_risky_wording_leading_in_description():
    e = _entry(description="The leading platform for AI security.")
    findings = detect_risky_wording(e)
    assert any(f["term"] == "leading" and f["field"] == "description" for f in findings)


def test_risky_wording_best_in_buyer_problems():
    e = _entry(buyer_problems=["Use the best AI security platform."])
    findings = detect_risky_wording(e)
    assert any(f["term"] == "best" and "buyer_problems" in f["field"] for f in findings)


@pytest.mark.parametrize("term", [
    "leading", "best", "dominant", "market-leading",
    "first", "only", "guaranteed", "proven", "complete", "fully",
])
def test_risky_wording_all_terms_detected(term):
    e = _entry(description=f"This is the {term} solution for AI security.")
    findings = detect_risky_wording(e)
    assert any(f["term"] == term for f in findings), f"Term '{term}' was not detected"


def test_risky_wording_clean_description():
    e = _entry(description="Scans ML models for adversarial vulnerabilities.")
    findings = detect_risky_wording(e)
    assert findings == []


def test_risky_wording_case_insensitive():
    e = _entry(description="The BEST AI security platform available.")
    findings = detect_risky_wording(e)
    assert any(f["term"] == "best" for f in findings)


def test_risky_wording_multiple_fields():
    e = _entry(
        description="The leading AI platform.",
        buyer_problems=["Find the best solution."],
    )
    findings = detect_risky_wording(e)
    assert any(f["field"] == "description" for f in findings)
    assert any("buyer_problems" in f["field"] for f in findings)


def test_risky_wording_finding_includes_field_term_text():
    e = _entry(description="The best ML security tool.")
    findings = detect_risky_wording(e)
    assert len(findings) >= 1
    f = findings[0]
    assert "field" in f
    assert "term" in f
    assert "text" in f


def test_risky_wording_no_false_positive_on_clean_buyer_problems():
    e = _entry(buyer_problems=[
        "Detect adversarial attacks on deployed models.",
        "Scan artifacts for malware before deployment.",
    ])
    findings = detect_risky_wording(e)
    assert findings == []


# ── build_report — entry fields ────────────────────────────────────────────────

def test_report_includes_entry_id():
    e = _entry()
    assert "test-vendor" in build_report(e)


def test_report_includes_name():
    e = _entry(name="Acme AI Security")
    assert "Acme AI Security" in build_report(e)


def test_report_includes_organization():
    e = _entry(organization="Acme Corporation")
    assert "Acme Corporation" in build_report(e)


def test_report_includes_category():
    e = _entry()
    assert "model-security" in build_report(e)


def test_report_includes_csa_member_false():
    e = _entry(csa_member=False)
    assert "false" in build_report(e)


def test_report_includes_csa_member_true():
    e = _entry(
        csa_member=True,
        review={"status": "verified", "verification_needed": []},
    )
    assert "true" in build_report(e)


# ── build_report — review metadata ────────────────────────────────────────────

def test_report_includes_review_status():
    e = _entry()
    assert "seed" in build_report(e)


def test_report_includes_verification_needed_fields():
    e = _entry()
    report = build_report(e)
    assert "csa_member" in report
    assert "pricing" in report
    assert "integrations" in report
    assert "description" in report


def test_report_includes_review_notes():
    e = _entry()
    assert "Requires human review" in build_report(e)


# ── build_report — flags ───────────────────────────────────────────────────────

def test_report_flags_missing_review_metadata():
    e = _entry(review=None)
    assert "Review metadata missing" in build_report(e)


def test_report_flags_csa_member_unverified_seed():
    e = _entry(
        csa_member=True,
        review={"status": "seed", "verification_needed": []},
    )
    assert "CSA member not verified" in build_report(e)


def test_report_flags_csa_member_unverified_no_review():
    e = _entry(csa_member=True, review=None)
    assert "CSA member not verified" in build_report(e)


def test_report_does_not_flag_csa_member_when_verified():
    e = _entry(
        csa_member=True,
        review={"status": "verified", "verification_needed": []},
    )
    assert "CSA member not verified" not in build_report(e)


def test_report_flags_missing_website():
    e = _entry(website="")
    assert "Website missing" in build_report(e)


def test_report_does_not_flag_website_when_present():
    e = _entry(website="https://example.com")
    assert "Website missing" not in build_report(e)


def test_report_flags_risky_wording():
    e = _entry(description="The leading AI security platform.")
    report = build_report(e)
    assert "Potential Wording Issues" in report
    assert "leading" in report


def test_report_no_wording_section_when_clean():
    e = _entry(description="Scans ML models for adversarial vulnerabilities.")
    assert "Potential Wording Issues" not in build_report(e)


def test_report_wording_guidance_does_not_rewrite_entry():
    e = _entry(description="The best AI security platform.")
    report = build_report(e)
    assert "does not rewrite entries automatically" in report


# ── build_report — advisory content ───────────────────────────────────────────

def test_report_includes_advisory_disclaimer():
    e = _entry()
    report = build_report(e)
    assert "Advisory only" in report or "advisory only" in report


def test_report_references_landscape_yaml():
    e = _entry()
    assert "data/landscape.yaml" in build_report(e)


def test_report_includes_human_approval_reminder():
    e = _entry()
    report = build_report(e)
    assert "human" in report.lower()


def test_report_includes_validate_command():
    e = _entry()
    assert "validate.py" in build_report(e)


def test_report_generated_date_present():
    e = _entry()
    report = build_report(e, today="2026-06-01")
    assert "2026-06-01" in report


# ── dry-run: must not write files ─────────────────────────────────────────────

def test_dry_run_does_not_create_files(tmp_path, capsys):
    landscape = _make_landscape()
    run_review(landscape.entries, dry_run=True, reviews_dir=tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_dry_run_prints_to_stdout(tmp_path, capsys):
    landscape = _make_landscape()
    run_review(landscape.entries, dry_run=True, reviews_dir=tmp_path)
    out = capsys.readouterr().out
    assert "Review Report" in out


def test_dry_run_multi_entry_separates_reports(tmp_path, capsys):
    landscape = _make_landscape(
        _make_entry(id="second-vendor", name="Second Vendor")
    )
    run_review(landscape.entries, dry_run=True, reviews_dir=tmp_path)
    out = capsys.readouterr().out
    assert out.count("Review Report") == len(landscape.entries)


def test_non_dry_run_writes_report_file(tmp_path):
    landscape = _make_landscape()
    run_review([landscape.entries[0]], dry_run=False, reviews_dir=tmp_path)
    files = list(tmp_path.iterdir())
    assert len(files) == 1
    assert files[0].suffix == ".md"


def test_non_dry_run_file_content_is_report(tmp_path):
    landscape = _make_landscape()
    run_review([landscape.entries[0]], dry_run=False, reviews_dir=tmp_path)
    content = next(tmp_path.iterdir()).read_text()
    assert "Review Report" in content
    assert "Advisory only" in content or "advisory only" in content


def test_run_review_returns_count(tmp_path):
    landscape = _make_landscape(
        _make_entry(id="second-vendor", name="Second Vendor")
    )
    count = run_review(landscape.entries, dry_run=True, reviews_dir=tmp_path)
    assert count == len(landscape.entries)


# ── data/landscape.yaml is not modified ──────────────────────────────────────

def test_landscape_yaml_not_modified_by_dry_run(tmp_path):
    landscape_path = Path(__file__).parents[2] / "data" / "landscape.yaml"
    content_before = landscape_path.read_bytes()

    landscape = _make_landscape()
    run_review(landscape.entries, dry_run=True, reviews_dir=tmp_path)

    assert landscape_path.read_bytes() == content_before, (
        "data/landscape.yaml was modified — review agent must never write to it"
    )


def test_landscape_yaml_not_modified_by_file_write(tmp_path):
    landscape_path = Path(__file__).parents[2] / "data" / "landscape.yaml"
    content_before = landscape_path.read_bytes()

    landscape = _make_landscape()
    run_review(landscape.entries, dry_run=False, reviews_dir=tmp_path)

    assert landscape_path.read_bytes() == content_before, (
        "data/landscape.yaml was modified — review agent must never write to it"
    )

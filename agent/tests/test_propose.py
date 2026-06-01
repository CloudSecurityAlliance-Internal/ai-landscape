"""
Tests for agent/propose.py — local proposal agent.

All tests use injected paths (tmp_path) so no real files in agent/proposals/
are created or modified.
"""
import os
from datetime import date
from pathlib import Path

import pytest
import yaml

from propose import (
    build_api_prompt,
    build_header,
    build_template_entry_yaml,
    generate_template,
    get_proposal_path,
    parse_api_response,
    run_template,
    slugify,
    suggest_categories,
    validate_api_entries,
    validate_category,
)
from schema import LandscapeFile

# All RFC-001 fields that must appear in every template entry
REQUIRED_RFC001_FIELDS = [
    "id", "name", "category", "organization", "description",
    "website", "github", "license", "pricing", "api_available",
    "vendor_type", "csa_member", "tags", "capability_tags",
    "buyer_problems", "integrations", "maestro_layers",
    "aicm_control_families", "added", "updated",
]


# ── Fixtures ───────────────────────────────────────────────────────────────────

def _make_landscape() -> LandscapeFile:
    return LandscapeFile.model_validate({
        "categories": [
            {"id": "model-security", "name": "Model Security", "area": "security-for-ai"},
            {"id": "prompt-defense", "name": "Prompt Defense", "area": "security-for-ai"},
            {"id": "ai-soc", "name": "AI SOC", "area": "ai-for-security"},
            {"id": "ai-governance", "name": "AI Governance", "area": "ai-governance-risk"},
        ],
        "entries": [],
    })


def _make_landscape_with_entry() -> LandscapeFile:
    return LandscapeFile.model_validate({
        "categories": [
            {"id": "model-security", "name": "Model Security"},
        ],
        "entries": [
            {
                "id": "existing-vendor",
                "name": "Existing Vendor",
                "category": "model-security",
                "organization": "Existing Corp",
                "description": "An existing vendor.",
                "website": "https://existing.example.com",
                "license": "proprietary",
                "pricing": "enterprise",
                "added": "2026-06-01",
                "updated": "2026-06-01",
            }
        ],
    })


# ── suggest_categories ─────────────────────────────────────────────────────────

def test_suggest_categories_prompt_injection():
    cats = {"prompt-defense", "model-security", "ai-soc"}
    result = suggest_categories("protect my LLM from prompt injection attacks", cats)
    assert "prompt-defense" in result


def test_suggest_categories_adversarial_ml():
    cats = {"model-security", "prompt-defense", "ai-soc"}
    result = suggest_categories("detect adversarial ml attacks on my model", cats)
    assert "model-security" in result


def test_suggest_categories_no_match_returns_fallback():
    cats = {"model-security", "prompt-defense", "ai-soc"}
    result = suggest_categories("completely unrelated query xyz", cats)
    assert len(result) > 0
    assert all(c in cats for c in result)


def test_suggest_categories_only_returns_valid_ids():
    cats = {"model-security"}
    result = suggest_categories("model attack", cats)
    assert all(c in cats for c in result)


def test_suggest_categories_no_duplicates():
    cats = {"prompt-defense", "model-security", "ai-soc"}
    result = suggest_categories("prompt inject jailbreak llm input", cats)
    assert len(result) == len(set(result))


# ── slugify ────────────────────────────────────────────────────────────────────

def test_slugify_basic():
    assert slugify("HiddenLayer") == "hiddenlayer"


def test_slugify_spaces_to_hyphens():
    assert slugify("My Vendor Name") == "my-vendor-name"


def test_slugify_truncates():
    long = "a" * 100
    result = slugify(long, max_len=10)
    assert len(result) <= 10


def test_slugify_strips_special_chars():
    assert slugify("Vendor! @#$") == "vendor"


# ── get_proposal_path ──────────────────────────────────────────────────────────

def test_proposal_path_is_under_proposals_dir(tmp_path):
    path = get_proposal_path("model-security", proposals_dir=tmp_path)
    assert path.parent == tmp_path


def test_proposal_path_contains_today(tmp_path):
    today = date.today().isoformat()
    path = get_proposal_path("model-security", proposals_dir=tmp_path)
    assert today in path.name


def test_proposal_path_contains_slug(tmp_path):
    path = get_proposal_path("my-slug", proposals_dir=tmp_path)
    assert "my-slug" in path.name


def test_proposal_path_has_yaml_extension(tmp_path):
    path = get_proposal_path("test", proposals_dir=tmp_path)
    assert path.suffix == ".yaml"


# ── build_header ───────────────────────────────────────────────────────────────

def test_build_header_contains_pending_review():
    header = build_header("category", "model-security")
    assert "PENDING REVIEW" in header


def test_build_header_contains_mode_and_target():
    header = build_header("category", "model-security")
    assert "category" in header
    assert "model-security" in header


def test_build_header_contains_landscape_yaml_reference():
    header = build_header("category", "model-security")
    assert "data/landscape.yaml" in header


def test_build_header_warns_about_csa_member():
    header = build_header("category", "model-security")
    assert "csa_member" in header


def test_build_header_contains_extra_lines():
    header = build_header("problem", "injection", extra_lines=["Custom note here"])
    assert "Custom note here" in header


def test_build_header_contains_today():
    header = build_header("category", "model-security")
    assert date.today().isoformat() in header


# ── build_template_entry_yaml ──────────────────────────────────────────────────

def test_template_entry_contains_all_rfc001_fields():
    entry_yaml = build_template_entry_yaml("model-security")
    for field in REQUIRED_RFC001_FIELDS:
        assert field in entry_yaml, f"Missing field: {field}"


def test_template_entry_has_correct_category():
    entry_yaml = build_template_entry_yaml("prompt-defense")
    assert "prompt-defense" in entry_yaml


def test_template_entry_name_hint_is_included():
    entry_yaml = build_template_entry_yaml("model-security", name_hint="HiddenLayer")
    assert "HiddenLayer" in entry_yaml


def test_template_entry_csa_member_is_false():
    entry_yaml = build_template_entry_yaml("model-security")
    assert "csa_member: false" in entry_yaml


def test_template_entry_contains_maestro_reference():
    entry_yaml = build_template_entry_yaml("model-security")
    assert "MAESTRO" in entry_yaml
    assert "L1-foundation-models" in entry_yaml


def test_template_entry_contains_aicm_reference():
    entry_yaml = build_template_entry_yaml("model-security")
    assert "AICM" in entry_yaml
    assert "GRM" in entry_yaml


def test_template_entry_is_parseable_yaml():
    raw = "proposals:\n" + build_template_entry_yaml("model-security")
    parsed = yaml.safe_load(raw)
    assert "proposals" in parsed
    entry = parsed["proposals"][0]
    assert entry["category"] == "model-security"
    assert entry["csa_member"] is False
    assert entry["api_available"] is False
    assert entry["maestro_layers"] == []
    assert entry["aicm_control_families"] == []


def test_template_entry_today_in_dates():
    entry_yaml = build_template_entry_yaml("model-security")
    today = date.today().isoformat()
    assert today in entry_yaml


# ── generate_template ──────────────────────────────────────────────────────────

def test_generate_template_has_proposals_key():
    output = generate_template("category", "model-security", ["model-security"])
    assert "proposals:" in output


def test_generate_template_has_pending_review():
    output = generate_template("category", "model-security", ["model-security"])
    assert "PENDING REVIEW" in output


def test_generate_template_includes_all_categories():
    output = generate_template("problem", "injection", ["prompt-defense", "agent-security"])
    assert "prompt-defense" in output
    assert "agent-security" in output


def test_generate_template_extra_header_lines():
    output = generate_template(
        "problem", "test", ["model-security"],
        extra_header_lines=["Problem: test", "Top match: model-security"],
    )
    assert "Problem: test" in output
    assert "Top match: model-security" in output


# ── dry-run: must not write files ─────────────────────────────────────────────

def test_dry_run_does_not_create_files(tmp_path, capsys):
    landscape = _make_landscape()
    run_template(
        mode="category",
        target="model-security",
        landscape=landscape,
        dry_run=True,
        proposals_dir=tmp_path,
    )
    assert list(tmp_path.iterdir()) == [], "dry-run must not write any files"
    captured = capsys.readouterr()
    assert "model-security" in captured.out


def test_dry_run_prints_to_stdout(tmp_path, capsys):
    landscape = _make_landscape()
    run_template(
        mode="category",
        target="model-security",
        landscape=landscape,
        dry_run=True,
        proposals_dir=tmp_path,
    )
    captured = capsys.readouterr()
    assert "proposals:" in captured.out
    assert "PENDING REVIEW" in captured.out


def test_non_dry_run_writes_proposal_file(tmp_path):
    landscape = _make_landscape()
    run_template(
        mode="category",
        target="model-security",
        landscape=landscape,
        dry_run=False,
        proposals_dir=tmp_path,
    )
    files = list(tmp_path.iterdir())
    assert len(files) == 1
    assert files[0].suffix == ".yaml"


def test_non_dry_run_file_contains_proposals(tmp_path):
    landscape = _make_landscape()
    run_template(
        mode="category",
        target="model-security",
        landscape=landscape,
        dry_run=False,
        proposals_dir=tmp_path,
    )
    content = next(tmp_path.iterdir()).read_text()
    assert "proposals:" in content
    assert "model-security" in content


# ── validate_category ──────────────────────────────────────────────────────────

def test_invalid_category_raises_value_error():
    landscape = _make_landscape()
    with pytest.raises(ValueError, match="Unknown category"):
        validate_category("does-not-exist", landscape)


def test_invalid_category_error_lists_valid_ids():
    landscape = _make_landscape()
    with pytest.raises(ValueError, match="model-security"):
        validate_category("does-not-exist", landscape)


def test_valid_category_does_not_raise():
    landscape = _make_landscape()
    validate_category("model-security", landscape)  # must not raise


# ── landscape YAML is never modified ─────────────────────────────────────────

def test_landscape_yaml_not_modified_by_dry_run(tmp_path):
    landscape_path = Path(__file__).parents[2] / "data" / "landscape.yaml"
    content_before = landscape_path.read_bytes()

    landscape = _make_landscape()
    run_template(
        mode="category",
        target="model-security",
        landscape=landscape,
        dry_run=True,
        proposals_dir=tmp_path,
    )

    assert landscape_path.read_bytes() == content_before


def test_landscape_yaml_not_modified_by_file_write(tmp_path):
    landscape_path = Path(__file__).parents[2] / "data" / "landscape.yaml"
    content_before = landscape_path.read_bytes()

    landscape = _make_landscape()
    run_template(
        mode="category",
        target="model-security",
        landscape=landscape,
        dry_run=False,
        proposals_dir=tmp_path,
    )

    assert landscape_path.read_bytes() == content_before


# ── run_template problem and vendor modes ────────────────────────────────────

def test_problem_mode_creates_file(tmp_path):
    landscape = _make_landscape()
    run_template(
        mode="problem",
        target="protect my LLM from prompt injection",
        landscape=landscape,
        dry_run=False,
        proposals_dir=tmp_path,
    )
    files = list(tmp_path.iterdir())
    assert len(files) == 1


def test_problem_mode_dry_run_output_mentions_problem(tmp_path, capsys):
    landscape = _make_landscape()
    run_template(
        mode="problem",
        target="protect my LLM from prompt injection",
        landscape=landscape,
        dry_run=True,
        proposals_dir=tmp_path,
    )
    out = capsys.readouterr().out
    assert "prompt injection" in out


def test_vendor_mode_dry_run_includes_vendor_name(tmp_path, capsys):
    landscape = _make_landscape()
    run_template(
        mode="vendor",
        target="HiddenLayer",
        landscape=landscape,
        dry_run=True,
        proposals_dir=tmp_path,
    )
    out = capsys.readouterr().out
    assert "HiddenLayer" in out


# ── parse_api_response ─────────────────────────────────────────────────────────

def test_parse_api_response_valid_json_list():
    raw = '[{"id": "test", "name": "Test"}]'
    result = parse_api_response(raw)
    assert result == [{"id": "test", "name": "Test"}]


def test_parse_api_response_strips_markdown_code_fences():
    raw = '```json\n[{"id": "x"}]\n```'
    result = parse_api_response(raw)
    assert result == [{"id": "x"}]


def test_parse_api_response_strips_bare_code_fences():
    raw = '```\n[{"id": "x"}]\n```'
    result = parse_api_response(raw)
    assert result == [{"id": "x"}]


def test_parse_api_response_invalid_json_returns_empty():
    assert parse_api_response("not json at all") == []


def test_parse_api_response_object_not_list_returns_empty():
    assert parse_api_response('{"id": "x"}') == []


def test_parse_api_response_empty_string_returns_empty():
    assert parse_api_response("") == []


# ── build_api_prompt ───────────────────────────────────────────────────────────

def test_build_api_prompt_contains_mode_target():
    landscape = _make_landscape()
    prompt = build_api_prompt("category", "model-security", landscape)
    assert "model-security" in prompt


def test_build_api_prompt_lists_categories():
    landscape = _make_landscape()
    prompt = build_api_prompt("category", "model-security", landscape)
    for cat in landscape.categories:
        assert cat.id in prompt


def test_build_api_prompt_contains_all_required_fields():
    landscape = _make_landscape()
    prompt = build_api_prompt("category", "model-security", landscape)
    for field in REQUIRED_RFC001_FIELDS:
        assert field in prompt, f"Missing field in prompt: {field}"


def test_build_api_prompt_instructs_csa_member_false():
    landscape = _make_landscape()
    prompt = build_api_prompt("category", "model-security", landscape)
    assert "csa_member" in prompt
    assert "false" in prompt.lower()


def test_build_api_prompt_problem_mode():
    landscape = _make_landscape()
    prompt = build_api_prompt("problem", "detect prompt injection", landscape)
    assert "detect prompt injection" in prompt


def test_build_api_prompt_vendor_mode():
    landscape = _make_landscape()
    prompt = build_api_prompt("vendor", "HiddenLayer", landscape)
    assert "HiddenLayer" in prompt


# ── validate_api_entries ───────────────────────────────────────────────────────

def test_validate_api_entries_rejects_existing_id():
    landscape = _make_landscape_with_entry()
    raw_entries = [{"id": "existing-vendor", "name": "Existing"}]
    valid, rejected = validate_api_entries(raw_entries, landscape)
    assert valid == []
    assert len(rejected) == 1
    assert "existing-vendor" in rejected[0][1]


def test_validate_api_entries_rejects_schema_invalid_entry():
    landscape = _make_landscape()
    raw_entries = [{"id": "bad", "name": "Missing required fields"}]
    valid, rejected = validate_api_entries(raw_entries, landscape)
    assert valid == []
    assert len(rejected) == 1


def test_validate_api_entries_accepts_valid_new_entry():
    landscape = _make_landscape()
    raw_entries = [{
        "id": "new-vendor",
        "name": "New Vendor",
        "category": "model-security",
        "organization": "New Corp",
        "description": "A new AI security vendor.",
        "website": "https://newvendor.example.com",
        "license": "proprietary",
        "pricing": "enterprise",
        "added": "2026-06-01",
        "updated": "2026-06-01",
    }]
    valid, rejected = validate_api_entries(raw_entries, landscape)
    assert len(valid) == 1
    assert rejected == []


def test_validate_api_entries_mixed_valid_and_invalid():
    landscape = _make_landscape()
    raw_entries = [
        {
            "id": "valid-vendor",
            "name": "Valid Vendor",
            "category": "model-security",
            "organization": "Valid Corp",
            "description": "A valid vendor.",
            "website": "https://valid.example.com",
            "license": "MIT",
            "pricing": "free",
            "added": "2026-06-01",
            "updated": "2026-06-01",
        },
        {"id": "invalid", "name": "no other fields"},
    ]
    valid, rejected = validate_api_entries(raw_entries, landscape)
    assert len(valid) == 1
    assert len(rejected) == 1

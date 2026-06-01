import pytest
from pydantic import ValidationError
from schema import (
    LandscapeEntry,
    LandscapeFile,
    ReviewMetadata,
    MAESTRO_LAYERS,
    AICM_FAMILIES,
)


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


# ── Existing tests (unchanged) ────────────────────────────────────────────────

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


def test_invalid_subcategory_for_category():
    data = {
        "categories": [
            {
                "id": "agentic-harnesses",
                "name": "Agentic Harnesses",
                "subcategories": [{"id": "multi-agent", "name": "Multi-Agent"}],
            }
        ],
        "entries": [_valid_entry(subcategory="nonexistent-sub")],
    }
    with pytest.raises(ValidationError, match="subcategory"):
        LandscapeFile(**data)


# ── RFC-001 field defaults ────────────────────────────────────────────────────

def test_rfc001_fields_default_empty():
    entry = LandscapeEntry(**_valid_entry())
    assert entry.capability_tags == []
    assert entry.buyer_problems == []
    assert entry.integrations == []
    assert entry.maestro_layers == []
    assert entry.aicm_control_families == []
    assert entry.csa_member is False
    assert entry.vendor_type is None


def test_csa_member_can_be_true():
    entry = LandscapeEntry(**_valid_entry(csa_member=True))
    assert entry.csa_member is True


def test_vendor_type_valid_values():
    for vt in ("ai-native", "cloud-native", "hybrid"):
        entry = LandscapeEntry(**_valid_entry(vendor_type=vt))
        assert entry.vendor_type == vt


def test_vendor_type_invalid_rejects():
    with pytest.raises(ValidationError):
        LandscapeEntry(**_valid_entry(vendor_type="startup"))


# ── MAESTRO layer validation ──────────────────────────────────────────────────

def test_maestro_layers_accepts_all_valid():
    for layer in MAESTRO_LAYERS:
        entry = LandscapeEntry(**_valid_entry(maestro_layers=[layer]))
        assert layer in entry.maestro_layers


def test_maestro_layers_accepts_multiple():
    layers = ["L1-foundation-models", "L6-security-controls"]
    entry = LandscapeEntry(**_valid_entry(maestro_layers=layers))
    assert entry.maestro_layers == layers


def test_maestro_layers_rejects_unknown():
    with pytest.raises(ValidationError, match="MAESTRO"):
        LandscapeEntry(**_valid_entry(maestro_layers=["L99-does-not-exist"]))


def test_maestro_layers_rejects_partial_match():
    with pytest.raises(ValidationError, match="MAESTRO"):
        LandscapeEntry(**_valid_entry(maestro_layers=["L1-foundation-models", "L99-bad"]))


def test_maestro_layers_empty_list_accepted():
    entry = LandscapeEntry(**_valid_entry(maestro_layers=[]))
    assert entry.maestro_layers == []


# ── AICM control family validation ───────────────────────────────────────────

def test_aicm_families_accepts_all_valid():
    for family in AICM_FAMILIES:
        entry = LandscapeEntry(**_valid_entry(aicm_control_families=[family]))
        assert family in entry.aicm_control_families


def test_aicm_families_accepts_multiple():
    families = ["TP", "GRM", "DSP"]
    entry = LandscapeEntry(**_valid_entry(aicm_control_families=families))
    assert entry.aicm_control_families == families


def test_aicm_families_rejects_unknown():
    with pytest.raises(ValidationError, match="AICM"):
        LandscapeEntry(**_valid_entry(aicm_control_families=["XYZ"]))


def test_aicm_families_rejects_partial_match():
    with pytest.raises(ValidationError, match="AICM"):
        LandscapeEntry(**_valid_entry(aicm_control_families=["TP", "BADONE"]))


def test_aicm_families_empty_list_accepted():
    entry = LandscapeEntry(**_valid_entry(aicm_control_families=[]))
    assert entry.aicm_control_families == []


# ── Category area and description ─────────────────────────────────────────────

def test_category_area_field():
    data = {
        "categories": [
            {
                "id": "model-security",
                "name": "Model Security & Integrity",
                "area": "security-for-ai",
                "description": "Protecting ML models from attack.",
            }
        ],
        "entries": [_valid_entry(category="model-security")],
    }
    lf = LandscapeFile(**data)
    cat = lf.categories[0]
    assert cat.area == "security-for-ai"
    assert cat.description == "Protecting ML models from attack."


def test_category_area_is_optional():
    data = _valid_landscape()
    lf = LandscapeFile(**data)
    assert lf.categories[0].area is None
    assert lf.categories[0].description is None


# ── Full RFC-001 entry round-trip ─────────────────────────────────────────────

def test_full_rfc001_entry():
    data = {
        "categories": [{"id": "model-security", "name": "Model Security", "area": "security-for-ai"}],
        "entries": [
            {
                "id": "test-vendor",
                "name": "Test Vendor",
                "category": "model-security",
                "organization": "Test Corp",
                "description": "Detects adversarial attacks on ML models.",
                "website": "https://testvendor.example.com",
                "license": "proprietary",
                "pricing": "enterprise",
                "api_available": True,
                "vendor_type": "ai-native",
                "csa_member": True,
                "tags": ["model-security", "adversarial-ml"],
                "capability_tags": ["ai-supply-chain"],
                "buyer_problems": ["Detect adversarial attacks on deployed models"],
                "integrations": ["AWS", "Azure"],
                "maestro_layers": ["L1-foundation-models", "L6-security-controls"],
                "aicm_control_families": ["TP", "SC"],
                "added": "2026-06-01",
                "updated": "2026-06-01",
            }
        ],
    }
    lf = LandscapeFile(**data)
    entry = lf.entries[0]
    assert entry.vendor_type == "ai-native"
    assert entry.csa_member is True
    assert entry.capability_tags == ["ai-supply-chain"]
    assert entry.buyer_problems == ["Detect adversarial attacks on deployed models"]
    assert entry.integrations == ["AWS", "Azure"]
    assert "L1-foundation-models" in entry.maestro_layers
    assert "TP" in entry.aicm_control_families


# ── Review metadata ───────────────────────────────────────────────────────────

def test_review_metadata_valid():
    rm = ReviewMetadata(
        status="seed",
        last_reviewed=None,
        reviewed_by=None,
        verification_needed=["csa_member", "pricing", "integrations", "description"],
        notes="Seed entry. Requires human review before production publication.",
    )
    assert rm.status == "seed"
    assert rm.last_reviewed is None
    assert rm.reviewed_by is None
    assert rm.verification_needed == ["csa_member", "pricing", "integrations", "description"]


def test_review_metadata_defaults_when_omitted():
    entry = LandscapeEntry(**_valid_entry())
    assert entry.review is None


def test_review_status_invalid_rejected():
    with pytest.raises(ValidationError):
        ReviewMetadata(status="approved")


def test_review_verification_needed_defaults_empty():
    rm = ReviewMetadata(status="needs-review")
    assert rm.verification_needed == []


def test_full_entry_with_review_metadata():
    data = _valid_landscape(
        review={
            "status": "seed",
            "last_reviewed": None,
            "reviewed_by": None,
            "verification_needed": ["csa_member", "pricing", "integrations", "description"],
            "notes": "Seed entry. Requires human review before production publication.",
        }
    )
    lf = LandscapeFile(**data)
    entry = lf.entries[0]
    assert entry.review is not None
    assert entry.review.status == "seed"
    assert "csa_member" in entry.review.verification_needed
    assert entry.review.last_reviewed is None

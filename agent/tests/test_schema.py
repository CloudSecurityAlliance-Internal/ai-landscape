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

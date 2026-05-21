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

#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import yaml
from pathlib import Path
from pydantic import ValidationError
from schema import LandscapeFile


def validate(yaml_path: str) -> bool:
    try:
        raw = Path(yaml_path).read_text()
        data = yaml.safe_load(raw)
        LandscapeFile.model_validate(data)
        print(f"✓ {yaml_path} is valid")
        return True
    except ValidationError as e:
        print(f"✗ Validation failed:\n{e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"✗ Error reading {yaml_path}: {e}", file=sys.stderr)
        return False


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "data/landscape.yaml"
    sys.exit(0 if validate(path) else 1)

from __future__ import annotations
from datetime import date
from typing import Literal, Optional
from pydantic import BaseModel, Field, model_validator


class Subcategory(BaseModel):
    id: str
    name: str


class Category(BaseModel):
    id: str
    name: str
    subcategories: list[Subcategory] = Field(default_factory=list)


class LandscapeEntry(BaseModel):
    id: str
    name: str
    category: str
    subcategory: Optional[str] = None
    organization: str
    description: str
    logo: Optional[str] = None
    website: str
    github: Optional[str] = None
    license: str
    pricing: Literal["free", "freemium", "paid", "enterprise"]
    api_available: bool = False
    tags: list[str] = Field(default_factory=list)
    added: date
    updated: date


class LandscapeFile(BaseModel):
    categories: list[Category]
    entries: list[LandscapeEntry]

    @model_validator(mode="after")
    def validate_entries(self) -> "LandscapeFile":
        category_map = {c.id: c for c in self.categories}

        seen: set[str] = set()
        dupes: set[str] = set()
        for entry in self.entries:
            (dupes if entry.id in seen else seen).add(entry.id)
        if dupes:
            raise ValueError(f"Duplicate entry IDs: {sorted(dupes)}")

        for entry in self.entries:
            if entry.category not in category_map:
                raise ValueError(
                    f"Entry '{entry.id}' has unknown category '{entry.category}'"
                )
            if entry.subcategory is not None:
                valid_subs = {s.id for s in category_map[entry.category].subcategories}
                if entry.subcategory not in valid_subs:
                    raise ValueError(
                        f"Entry '{entry.id}' has subcategory '{entry.subcategory}' "
                        f"not in category '{entry.category}'"
                    )

        return self

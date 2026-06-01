from __future__ import annotations
from datetime import date
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator, model_validator

# MAESTRO layer identifiers (CSA AI threat modeling framework)
MAESTRO_LAYERS: frozenset[str] = frozenset({
    "L1-foundation-models",
    "L2-data-operations",
    "L3-agent-frameworks",
    "L4-deployment-infrastructure",
    "L5-observability-feedback",
    "L6-security-controls",
    "L7-ecosystem-governance",
})

# AICM control family identifiers (CSA AI Controls Matrix)
AICM_FAMILIES: frozenset[str] = frozenset({
    "GRM",  # Governance & Risk Management
    "CAI",  # Compliance & Assurance
    "IAM",  # Identity & Access Management
    "DSP",  # Data Security & Privacy
    "TP",   # Threat Protection
    "INS",  # Infrastructure Security
    "IRS",  # Incident Response
    "SC",   # Supply Chain Security
})


class Subcategory(BaseModel):
    id: str
    name: str


class Category(BaseModel):
    id: str
    name: str
    area: Optional[str] = None
    description: Optional[str] = None
    subcategories: list[Subcategory] = Field(default_factory=list)


class LandscapeEntry(BaseModel):
    # Core identity
    id: str
    name: str
    category: str
    subcategory: Optional[str] = None
    organization: str
    description: str
    logo: Optional[str] = None
    website: str
    github: Optional[str] = None

    # Licensing and pricing
    license: str
    pricing: Literal["free", "freemium", "paid", "enterprise"]
    api_available: bool = False

    # Free-form capability tags (existing convention)
    tags: list[str] = Field(default_factory=list)

    # Timestamps
    added: date
    updated: date

    # RFC-001 extensions
    capability_tags: list[str] = Field(default_factory=list)
    buyer_problems: list[str] = Field(default_factory=list)
    integrations: list[str] = Field(default_factory=list)
    maestro_layers: list[str] = Field(default_factory=list)
    aicm_control_families: list[str] = Field(default_factory=list)
    csa_member: bool = False
    vendor_type: Optional[Literal["ai-native", "cloud-native", "hybrid"]] = None

    @field_validator("maestro_layers", mode="after")
    @classmethod
    def validate_maestro_layers(cls, v: list[str]) -> list[str]:
        if invalid := [x for x in v if x not in MAESTRO_LAYERS]:
            raise ValueError(
                f"Unknown MAESTRO layer(s): {sorted(invalid)}. "
                f"Valid: {sorted(MAESTRO_LAYERS)}"
            )
        return v

    @field_validator("aicm_control_families", mode="after")
    @classmethod
    def validate_aicm_families(cls, v: list[str]) -> list[str]:
        if invalid := [x for x in v if x not in AICM_FAMILIES]:
            raise ValueError(
                f"Unknown AICM control family/families: {sorted(invalid)}. "
                f"Valid: {sorted(AICM_FAMILIES)}"
            )
        return v


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

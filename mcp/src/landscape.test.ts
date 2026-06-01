import { describe, it, expect, beforeAll } from "vitest";
import * as path from "path";
import { fileURLToPath } from "url";
import { loadLandscape, listEntries, searchEntries, getStats, getCoverageMap } from "./landscape.js";
import type { Landscape } from "./landscape.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const YAML_PATH = path.resolve(__dirname, "../../data/landscape.yaml");

let landscape: Landscape;

beforeAll(() => {
  landscape = loadLandscape(YAML_PATH);
});

describe("loadLandscape", () => {
  it("loads categories", () => {
    expect(landscape.categories.length).toBeGreaterThan(0);
  });
  it("loads entries", () => {
    expect(landscape.entries.length).toBeGreaterThan(0);
  });
  it("loads category area", () => {
    const cat = landscape.categories.find((c) => c.id === "model-security");
    expect(cat?.area).toBe("security-for-ai");
  });
  it("loads category description", () => {
    const cat = landscape.categories.find((c) => c.id === "model-security");
    expect(typeof cat?.description).toBe("string");
    expect(cat!.description!.length).toBeGreaterThan(0);
  });
});

describe("listEntries", () => {
  it("returns all entries with no filters", () => {
    expect(listEntries(landscape, {}).length).toBe(landscape.entries.length);
  });
  it("filters by category", () => {
    const results = listEntries(landscape, { category: "agentic-harnesses" });
    results.forEach((e) => expect(e.category).toBe("agentic-harnesses"));
  });
  it("filters by pricing", () => {
    const results = listEntries(landscape, { pricing: "freemium" });
    results.forEach((e) => expect(e.pricing).toBe("freemium"));
  });
  it("filters by license", () => {
    const results = listEntries(landscape, { license: "MIT" });
    results.forEach((e) => expect(e.license).toBe("MIT"));
  });
  it("returns empty array when no match", () => {
    expect(listEntries(landscape, { category: "nonexistent" })).toHaveLength(0);
  });

  it("filters by area", () => {
    const results = listEntries(landscape, { area: "security-for-ai" });
    expect(results.length).toBeGreaterThan(0);
    const securityForAiCategoryIds = landscape.categories
      .filter((c) => c.area === "security-for-ai")
      .map((c) => c.id);
    results.forEach((e) => expect(securityForAiCategoryIds).toContain(e.category));
  });

  it("area filter returns no results for unknown area", () => {
    expect(listEntries(landscape, { area: "nonexistent-area" })).toHaveLength(0);
  });

  it("filters by csa_member false", () => {
    const results = listEntries(landscape, { csa_member: false });
    expect(results.length).toBeGreaterThan(0);
    results.forEach((e) => expect(e.csa_member).toBe(false));
  });

  it("filters by vendor_type", () => {
    const results = listEntries(landscape, { vendor_type: "ai-native" });
    expect(results.length).toBeGreaterThan(0);
    results.forEach((e) => expect(e.vendor_type).toBe("ai-native"));
  });

  it("filters by capability_tags using any-match", () => {
    const results = listEntries(landscape, { capability_tags: ["ai-supply-chain"] });
    expect(results.length).toBeGreaterThan(0);
    results.forEach((e) => expect(e.capability_tags).toContain("ai-supply-chain"));
  });

  it("capability_tags any-match returns entries that have any of the listed tags", () => {
    const results = listEntries(landscape, { capability_tags: ["ai-supply-chain", "agent-security"] });
    expect(results.length).toBeGreaterThan(0);
    results.forEach((e) => {
      const hasAny = ["ai-supply-chain", "agent-security"].some((t) => (e.capability_tags ?? []).includes(t));
      expect(hasAny).toBe(true);
    });
  });

  it("filters by integrations using any-match", () => {
    const results = listEntries(landscape, { integrations: ["AWS"] });
    expect(results.length).toBeGreaterThan(0);
    results.forEach((e) => expect(e.integrations).toContain("AWS"));
  });

  it("filters by maestro_layers using any-match", () => {
    const results = listEntries(landscape, { maestro_layers: ["L6-security-controls"] });
    expect(results.length).toBeGreaterThan(0);
    results.forEach((e) => expect(e.maestro_layers).toContain("L6-security-controls"));
  });

  it("filters by aicm_control_families using any-match", () => {
    const results = listEntries(landscape, { aicm_control_families: ["TP"] });
    expect(results.length).toBeGreaterThan(0);
    results.forEach((e) => expect(e.aicm_control_families).toContain("TP"));
  });

  it("aicm_control_families any-match: entry with one matching family is included", () => {
    const results = listEntries(landscape, { aicm_control_families: ["IAM", "SC"] });
    expect(results.length).toBeGreaterThan(0);
    results.forEach((e) => {
      const families = e.aicm_control_families ?? [];
      expect(families.includes("IAM") || families.includes("SC")).toBe(true);
    });
  });
});

describe("searchEntries", () => {
  it("finds entries by name substring", () => {
    const results = searchEntries(landscape, "Lakera");
    expect(results.some((e) => e.name.toLowerCase().includes("lakera") || e.organization.toLowerCase().includes("lakera"))).toBe(true);
  });
  it("returns empty for no match", () => {
    expect(searchEntries(landscape, "xyzzy_no_match_99999")).toHaveLength(0);
  });
  it("is case-insensitive", () => {
    const upper = searchEntries(landscape, "LAKERA");
    const lower = searchEntries(landscape, "lakera");
    expect(upper.length).toBe(lower.length);
  });
  it("searches across buyer_problems", () => {
    const results = searchEntries(landscape, "jailbreak");
    expect(results.length).toBeGreaterThan(0);
  });
  it("searches across capability_tags", () => {
    const results = searchEntries(landscape, "ai-supply-chain");
    expect(results.length).toBeGreaterThan(0);
  });
  it("searches across integrations", () => {
    const results = searchEntries(landscape, "SageMaker");
    expect(results.length).toBeGreaterThan(0);
  });
  it("searches across maestro_layers", () => {
    const results = searchEntries(landscape, "L6-security-controls");
    expect(results.length).toBeGreaterThan(0);
  });
  it("searches across aicm_control_families", () => {
    const results = searchEntries(landscape, "IAM");
    expect(results.length).toBeGreaterThan(0);
  });
  it("searches across vendor_type", () => {
    const results = searchEntries(landscape, "ai-native");
    expect(results.length).toBeGreaterThan(0);
  });
});

describe("getStats", () => {
  it("returns correct total", () => {
    expect(getStats(landscape).total_entries).toBe(landscape.entries.length);
  });
  it("includes per_category counts", () => {
    const stats = getStats(landscape);
    expect(typeof stats.per_category).toBe("object");
  });
  it("includes per_area counts", () => {
    const stats = getStats(landscape);
    expect(typeof stats.per_area).toBe("object");
    expect(Object.keys(stats.per_area).length).toBeGreaterThan(0);
    expect(stats.per_area["security-for-ai"]).toBeGreaterThan(0);
  });
  it("includes csa_member_count", () => {
    const stats = getStats(landscape);
    expect(typeof stats.csa_member_count).toBe("number");
    expect(stats.csa_member_count).toBeGreaterThanOrEqual(0);
  });
  it("includes per_vendor_type counts", () => {
    const stats = getStats(landscape);
    expect(typeof stats.per_vendor_type).toBe("object");
    expect(Object.keys(stats.per_vendor_type).length).toBeGreaterThan(0);
  });
  it("per_area total matches total_entries", () => {
    const stats = getStats(landscape);
    const areaTotal = Object.values(stats.per_area).reduce((a, b) => a + b, 0);
    expect(areaTotal).toBe(stats.total_entries);
  });
});

describe("getCoverageMap", () => {
  it("returns by_category coverage", () => {
    const coverage = getCoverageMap(landscape);
    expect(typeof coverage.by_category).toBe("object");
    expect(coverage.by_category["model-security"]).toBeGreaterThan(0);
  });
  it("returns by_maestro_layer coverage", () => {
    const coverage = getCoverageMap(landscape);
    expect(typeof coverage.by_maestro_layer).toBe("object");
    expect(coverage.by_maestro_layer["L6-security-controls"]).toBeGreaterThan(0);
  });
  it("returns by_aicm_family coverage", () => {
    const coverage = getCoverageMap(landscape);
    expect(typeof coverage.by_aicm_family).toBe("object");
    expect(coverage.by_aicm_family["TP"]).toBeGreaterThan(0);
  });
  it("returns integration_counts", () => {
    const coverage = getCoverageMap(landscape);
    expect(typeof coverage.integration_counts).toBe("object");
    expect(coverage.integration_counts["AWS"]).toBeGreaterThan(0);
  });
  it("returns capability_tag_counts", () => {
    const coverage = getCoverageMap(landscape);
    expect(typeof coverage.capability_tag_counts).toBe("object");
    expect(Object.keys(coverage.capability_tag_counts).length).toBeGreaterThan(0);
  });
  it("by_category totals match entry count", () => {
    const coverage = getCoverageMap(landscape);
    const catTotal = Object.values(coverage.by_category).reduce((a, b) => a + b, 0);
    expect(catTotal).toBe(landscape.entries.length);
  });
});

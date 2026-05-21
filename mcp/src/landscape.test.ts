import { describe, it, expect, beforeAll } from "vitest";
import * as path from "path";
import { fileURLToPath } from "url";
import { loadLandscape, listEntries, searchEntries, getStats } from "./landscape.js";
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
});

describe("searchEntries", () => {
  it("finds entries by name substring", () => {
    const results = searchEntries(landscape, "Claude");
    expect(results.some((e) => e.name.includes("Claude"))).toBe(true);
  });
  it("returns empty for no match", () => {
    expect(searchEntries(landscape, "xyzzy_no_match_99999")).toHaveLength(0);
  });
  it("is case-insensitive", () => {
    const upper = searchEntries(landscape, "CLAUDE");
    const lower = searchEntries(landscape, "claude");
    expect(upper.length).toBe(lower.length);
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
});

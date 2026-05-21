import * as fs from "fs";
import * as yaml from "js-yaml";

export interface Subcategory {
  id: string;
  name: string;
}

export interface Category {
  id: string;
  name: string;
  subcategories?: Subcategory[];
}

export interface Entry {
  id: string;
  name: string;
  category: string;
  subcategory?: string;
  organization: string;
  description: string;
  logo?: string;
  website: string;
  github?: string;
  license: string;
  pricing: string;
  api_available?: boolean;
  tags?: string[];
  added: string;
  updated: string;
}

export interface Landscape {
  categories: Category[];
  entries: Entry[];
}

export function loadLandscape(yamlPath: string): Landscape {
  const content = fs.readFileSync(yamlPath, "utf8");
  return yaml.load(content) as Landscape;
}

export interface EntryFilters {
  category?: string;
  subcategory?: string;
  tags?: string[];
  pricing?: string;
  license?: string;
  api_available?: boolean;
}

export function listEntries(landscape: Landscape, filters: EntryFilters): Entry[] {
  return landscape.entries.filter((e) => {
    if (filters.category && e.category !== filters.category) return false;
    if (filters.subcategory && e.subcategory !== filters.subcategory) return false;
    if (filters.pricing && e.pricing !== filters.pricing) return false;
    if (filters.license && e.license !== filters.license) return false;
    if (filters.api_available !== undefined && e.api_available !== filters.api_available) return false;
    if (filters.tags?.length) {
      const entryTags = e.tags ?? [];
      if (!filters.tags.every((t) => entryTags.includes(t))) return false;
    }
    return true;
  });
}

export function searchEntries(landscape: Landscape, query: string): Entry[] {
  const q = query.toLowerCase();
  return landscape.entries.filter(
    (e) =>
      e.name.toLowerCase().includes(q) ||
      e.description.toLowerCase().includes(q) ||
      e.organization.toLowerCase().includes(q) ||
      (e.tags ?? []).some((t) => t.toLowerCase().includes(q))
  );
}

export function getStats(landscape: Landscape) {
  const per_category: Record<string, number> = {};
  for (const cat of landscape.categories) {
    per_category[cat.id] = landscape.entries.filter((e) => e.category === cat.id).length;
  }
  const last_updated =
    landscape.entries
      .map((e) => e.updated)
      .sort()
      .reverse()[0] ?? null;
  return { total_entries: landscape.entries.length, per_category, last_updated };
}

import * as fs from "fs";
import * as yaml from "js-yaml";

export interface Subcategory {
  id: string;
  name: string;
}

export interface Category {
  id: string;
  name: string;
  area?: string;
  description?: string;
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
  capability_tags?: string[];
  buyer_problems?: string[];
  integrations?: string[];
  maestro_layers?: string[];
  aicm_control_families?: string[];
  csa_member?: boolean;
  vendor_type?: string;
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
  area?: string;
  csa_member?: boolean;
  vendor_type?: string;
  capability_tags?: string[];
  integrations?: string[];
  maestro_layers?: string[];
  aicm_control_families?: string[];
}

function anyMatch(entryValues: string[] | undefined, filterValues: string[]): boolean {
  const vals = entryValues ?? [];
  return filterValues.some((f) => vals.includes(f));
}

export function listEntries(landscape: Landscape, filters: EntryFilters): Entry[] {
  const categoryAreaMap: Record<string, string> = {};
  for (const cat of landscape.categories) {
    if (cat.area) categoryAreaMap[cat.id] = cat.area;
  }

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
    if (filters.area) {
      if (categoryAreaMap[e.category] !== filters.area) return false;
    }
    if (filters.csa_member !== undefined && e.csa_member !== filters.csa_member) return false;
    if (filters.vendor_type && e.vendor_type !== filters.vendor_type) return false;
    if (filters.capability_tags?.length && !anyMatch(e.capability_tags, filters.capability_tags)) return false;
    if (filters.integrations?.length && !anyMatch(e.integrations, filters.integrations)) return false;
    if (filters.maestro_layers?.length && !anyMatch(e.maestro_layers, filters.maestro_layers)) return false;
    if (filters.aicm_control_families?.length && !anyMatch(e.aicm_control_families, filters.aicm_control_families)) return false;
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
      (e.tags ?? []).some((t) => t.toLowerCase().includes(q)) ||
      (e.capability_tags ?? []).some((t) => t.toLowerCase().includes(q)) ||
      (e.buyer_problems ?? []).some((t) => t.toLowerCase().includes(q)) ||
      (e.integrations ?? []).some((t) => t.toLowerCase().includes(q)) ||
      (e.maestro_layers ?? []).some((t) => t.toLowerCase().includes(q)) ||
      (e.aicm_control_families ?? []).some((t) => t.toLowerCase().includes(q)) ||
      (e.vendor_type ?? "").toLowerCase().includes(q)
  );
}

export function getStats(landscape: Landscape) {
  const per_category: Record<string, number> = {};
  for (const cat of landscape.categories) {
    per_category[cat.id] = landscape.entries.filter((e) => e.category === cat.id).length;
  }

  const per_area: Record<string, number> = {};
  const categoryAreaMap: Record<string, string> = {};
  for (const cat of landscape.categories) {
    if (cat.area) categoryAreaMap[cat.id] = cat.area;
  }
  for (const e of landscape.entries) {
    const area = categoryAreaMap[e.category];
    if (area) per_area[area] = (per_area[area] ?? 0) + 1;
  }

  const csa_member_count = landscape.entries.filter((e) => e.csa_member === true).length;

  const per_vendor_type: Record<string, number> = {};
  for (const e of landscape.entries) {
    if (e.vendor_type) {
      per_vendor_type[e.vendor_type] = (per_vendor_type[e.vendor_type] ?? 0) + 1;
    }
  }

  const last_updated =
    landscape.entries
      .map((e) => e.updated)
      .sort()
      .reverse()[0] ?? null;

  return { total_entries: landscape.entries.length, per_category, per_area, csa_member_count, per_vendor_type, last_updated };
}

export function getCoverageMap(landscape: Landscape) {
  const by_category: Record<string, number> = {};
  for (const cat of landscape.categories) {
    by_category[cat.id] = landscape.entries.filter((e) => e.category === cat.id).length;
  }

  const by_maestro_layer: Record<string, number> = {};
  const by_aicm_family: Record<string, number> = {};
  const integration_counts: Record<string, number> = {};
  const capability_tag_counts: Record<string, number> = {};

  for (const e of landscape.entries) {
    for (const layer of e.maestro_layers ?? []) {
      by_maestro_layer[layer] = (by_maestro_layer[layer] ?? 0) + 1;
    }
    for (const family of e.aicm_control_families ?? []) {
      by_aicm_family[family] = (by_aicm_family[family] ?? 0) + 1;
    }
    for (const integration of e.integrations ?? []) {
      integration_counts[integration] = (integration_counts[integration] ?? 0) + 1;
    }
    for (const tag of e.capability_tags ?? []) {
      capability_tag_counts[tag] = (capability_tag_counts[tag] ?? 0) + 1;
    }
  }

  return { by_category, by_maestro_layer, by_aicm_family, integration_counts, capability_tag_counts };
}

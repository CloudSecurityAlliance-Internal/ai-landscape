import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import * as path from "path";
import { fileURLToPath } from "url";
import {
  loadLandscape,
  listEntries,
  searchEntries,
  getStats,
  getCoverageMap,
} from "./landscape.js";
import type { EntryFilters } from "./landscape.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const YAML_PATH =
  process.env.LANDSCAPE_YAML ??
  path.resolve(__dirname, "../../data/landscape.yaml");

const landscape = loadLandscape(YAML_PATH);

const server = new Server(
  { name: "csa-ai-landscape", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "list_categories",
      description: "List all landscape categories with entry counts, area, and description",
      inputSchema: { type: "object" as const, properties: {} },
    },
    {
      name: "list_entries",
      description:
        "List entries with optional filters. All parameters are optional. Array filters (capability_tags, integrations, maestro_layers, aicm_control_families) use any-match semantics.",
      inputSchema: {
        type: "object" as const,
        properties: {
          category: { type: "string", description: "Category ID (exact match)" },
          subcategory: { type: "string", description: "Subcategory ID" },
          tags: { type: "array", items: { type: "string" }, description: "All tags must match" },
          pricing: { type: "string", enum: ["free", "freemium", "paid", "enterprise"] },
          license: { type: "string", description: "SPDX identifier or 'proprietary'" },
          api_available: { type: "boolean" },
          area: { type: "string", enum: ["security-for-ai", "ai-for-security", "ai-governance-risk"], description: "Landscape area (matches via category)" },
          csa_member: { type: "boolean", description: "Filter by CSA membership status" },
          vendor_type: { type: "string", enum: ["ai-native", "cloud-native", "hybrid"], description: "Vendor type (exact match)" },
          capability_tags: { type: "array", items: { type: "string" }, description: "Any-match: entry must have at least one of these capability tags" },
          integrations: { type: "array", items: { type: "string" }, description: "Any-match: entry must support at least one of these integrations" },
          maestro_layers: { type: "array", items: { type: "string" }, description: "Any-match: entry must cover at least one of these MAESTRO layers" },
          aicm_control_families: { type: "array", items: { type: "string" }, description: "Any-match: entry must address at least one of these AICM control families" },
        },
      },
    },
    {
      name: "get_entry",
      description: "Get full details for a single entry by ID",
      inputSchema: {
        type: "object" as const,
        properties: { id: { type: "string" } },
        required: ["id"],
      },
    },
    {
      name: "search_entries",
      description: "Full-text search across name, description, organization, tags, capability_tags, buyer_problems, integrations, maestro_layers, aicm_control_families, and vendor_type",
      inputSchema: {
        type: "object" as const,
        properties: { query: { type: "string" } },
        required: ["query"],
      },
    },
    {
      name: "get_stats",
      description: "Entry counts by category, area, vendor type, CSA membership, and last-updated date",
      inputSchema: { type: "object" as const, properties: {} },
    },
    {
      name: "get_coverage_map",
      description: "Coverage counts by MAESTRO layer, AICM control family, integration, and capability tag",
      inputSchema: { type: "object" as const, properties: {} },
    },
  ],
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  const a = (args ?? {}) as Record<string, unknown>;

  switch (name) {
    case "list_categories": {
      const stats = getStats(landscape);
      return {
        content: [
          {
            type: "text" as const,
            text: JSON.stringify(
              landscape.categories.map((cat) => ({
                id: cat.id,
                name: cat.name,
                area: cat.area,
                description: cat.description,
                entry_count: stats.per_category[cat.id] ?? 0,
              })),
              null,
              2
            ),
          },
        ],
      };
    }

    case "list_entries": {
      const filters: EntryFilters = {
        category: a.category as string | undefined,
        subcategory: a.subcategory as string | undefined,
        tags: a.tags as string[] | undefined,
        pricing: a.pricing as string | undefined,
        license: a.license as string | undefined,
        api_available: a.api_available as boolean | undefined,
        area: a.area as string | undefined,
        csa_member: a.csa_member as boolean | undefined,
        vendor_type: a.vendor_type as string | undefined,
        capability_tags: a.capability_tags as string[] | undefined,
        integrations: a.integrations as string[] | undefined,
        maestro_layers: a.maestro_layers as string[] | undefined,
        aicm_control_families: a.aicm_control_families as string[] | undefined,
      };
      const entries = listEntries(landscape, filters);
      return {
        content: [
          {
            type: "text" as const,
            text: JSON.stringify(
              entries.map((e) => ({
                id: e.id,
                name: e.name,
                description: e.description,
                category: e.category,
                organization: e.organization,
                vendor_type: e.vendor_type,
                csa_member: e.csa_member,
                tags: e.tags,
                capability_tags: e.capability_tags,
                maestro_layers: e.maestro_layers,
                aicm_control_families: e.aicm_control_families,
              })),
              null,
              2
            ),
          },
        ],
      };
    }

    case "get_entry": {
      const entry = landscape.entries.find((e) => e.id === a.id);
      if (!entry) throw new Error(`Entry '${a.id}' not found`);
      return { content: [{ type: "text" as const, text: JSON.stringify(entry, null, 2) }] };
    }

    case "search_entries": {
      if (!a.query) throw new Error("query is required");
      const results = searchEntries(landscape, a.query as string);
      return {
        content: [
          {
            type: "text" as const,
            text: JSON.stringify(
              results.map((e) => ({
                id: e.id,
                name: e.name,
                description: e.description,
                category: e.category,
                organization: e.organization,
                tags: e.tags,
                capability_tags: e.capability_tags,
              })),
              null,
              2
            ),
          },
        ],
      };
    }

    case "get_stats":
      return { content: [{ type: "text" as const, text: JSON.stringify(getStats(landscape), null, 2) }] };

    case "get_coverage_map":
      return { content: [{ type: "text" as const, text: JSON.stringify(getCoverageMap(landscape), null, 2) }] };

    default:
      throw new Error(`Unknown tool: ${name}`);
  }
});

const transport = new StdioServerTransport();
await server.connect(transport);

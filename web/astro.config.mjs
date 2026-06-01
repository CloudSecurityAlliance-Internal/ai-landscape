import { defineConfig } from "astro/config";

const isGitHubActions = process.env.GITHUB_ACTIONS === "true";

export default defineConfig({
  output: "static",
  site: "https://joshbuker.github.io/ai-landscape",
  base: isGitHubActions ? "/ai-landscape" : undefined,
});

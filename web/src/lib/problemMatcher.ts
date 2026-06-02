export interface EntryMatchData {
  name: string;
  organization: string;
  category: string;
  categoryName: string;
  description: string;
  tags: string[];
  capability_tags: string[];
  buyer_problems: string[];
  integrations: string[];
  maestro_layers: string[];
  aicm_control_families: string[];
}

export interface MatchResult {
  tier: "strong" | "possible" | "none";
  reason: string;
  score: number;
}

// Two-character acronyms that are meaningful and should not be filtered
const KEEP_SHORT: Set<string> = new Set(["ai", "ml", "it", "ot"]);

const STOPWORDS: Set<string> = new Set([
  "a", "an", "and", "are", "as", "at",
  "be", "for", "from",
  "how", "i", "in", "is", "it",
  "me", "my",
  "need", "needs", "not",
  "of", "on", "or", "our",
  "real",
  "the", "thing", "things", "to",
  "use", "using",
  "we", "with", "without",
]);

function normalize(text: string): string {
  return text.toLowerCase().replace(/[^a-z0-9\s]/g, " ").replace(/\s+/g, " ").trim();
}

function tokenize(query: string): string[] {
  return normalize(query)
    .split(" ")
    .filter((t) => {
      if (t.length === 0) return false;
      if (t.length === 1) return false;
      if (t.length === 2) return KEEP_SHORT.has(t);
      if (STOPWORDS.has(t)) return false;
      return true;
    });
}

// Synonym expansion: each key expands into a list of terms also searched
const SYNONYMS: Record<string, string[]> = {
  // Prompt injection
  "prompt": ["prompt injection", "injection", "prompt"],
  "injection": ["injection", "prompt injection", "inject"],
  // Jailbreak
  "jailbreak": ["jailbreak", "jailbreaking", "adversarial input", "adversarial"],
  "jailbreaking": ["jailbreak", "jailbreaking", "adversarial"],
  // Agent / agentic
  "agent": ["agent", "agentic", "copilot", "autonomous", "ai agent"],
  "agents": ["agent", "agentic", "copilot", "autonomous"],
  "agentic": ["agentic", "agent", "copilot", "autonomous"],
  "copilot": ["copilot", "agent", "agentic"],
  // Non-human identity
  "nhi": ["nhi", "non-human", "non human", "service account", "machine identity", "workload identity"],
  "non-human": ["nhi", "non-human", "service account", "machine identity"],
  "nonhuman": ["nhi", "non-human", "service account", "machine identity"],
  "service": ["service account", "workload", "service"],
  // RAG
  "rag": ["rag", "retrieval", "vector store", "vector database", "retrieval augmented", "embedding"],
  "retrieval": ["retrieval", "rag", "vector store", "vector database"],
  "vector": ["vector", "rag", "retrieval", "embedding"],
  // Data leakage / exfiltration
  "leakage": ["leakage", "exfiltration", "dlp", "data loss", "data leak"],
  "exfiltration": ["exfiltration", "leakage", "dlp", "data loss"],
  "dlp": ["dlp", "data loss prevention", "exfiltration", "leakage"],
  "leak": ["leak", "leakage", "exfiltration", "data loss"],
  // Sensitive data / PII
  "sensitive": ["sensitive", "pii", "phi", "secret", "credential", "confidential"],
  "pii": ["pii", "sensitive", "personal data", "phi", "personally identifiable"],
  "phi": ["phi", "pii", "sensitive", "health data", "hipaa"],
  "secret": ["secret", "credential", "sensitive", "key", "token"],
  "credential": ["credential", "secret", "sensitive", "token", "password"],
  // SOC / security operations
  "soc": ["soc", "security operations", "detection", "siem", "soar", "security operations center"],
  "siem": ["siem", "soc", "security operations", "detection", "log management"],
  "soar": ["soar", "soc", "automation", "orchestration", "playbook"],
  // Threat detection
  "threat": ["threat", "detection", "anomaly", "attack", "malicious", "adversarial"],
  "detection": ["detection", "threat", "anomaly", "monitoring", "alert"],
  "anomaly": ["anomaly", "detection", "threat", "behavioral"],
  // Vulnerability / exposure
  "vulnerability": ["vulnerability", "cve", "exposure", "risk", "vuln", "weakness"],
  "vuln": ["vulnerability", "cve", "exposure", "vuln"],
  "cve": ["cve", "vulnerability", "patch", "exposure"],
  "exposure": ["exposure", "vulnerability", "risk", "attack surface"],
  "patch": ["patch", "vulnerability", "cve", "remediation"],
  // Governance / compliance
  "governance": ["governance", "policy", "compliance", "audit", "regulatory", "accountability"],
  "compliance": ["compliance", "regulatory", "audit", "governance", "gdpr", "eu ai act", "nist", "iso"],
  "regulatory": ["regulatory", "compliance", "audit", "governance"],
  "audit": ["audit", "compliance", "governance", "trail", "logging"],
  "policy": ["policy", "governance", "rule", "enforcement"],
  // Model risk
  "model": ["model", "model risk", "ml model", "foundation model", "llm"],
  "risk": ["risk", "exposure", "vulnerability", "risk quantification", "risk assessment"],
  // Observability / monitoring
  "observability": ["observability", "monitoring", "tracing", "drift", "performance", "logging"],
  "monitoring": ["monitoring", "observability", "tracing", "drift", "alerting"],
  "tracing": ["tracing", "observability", "monitoring", "logging"],
  "drift": ["drift", "monitoring", "observability", "model performance"],
  // Red teaming
  "red": ["red team", "red-team", "adversarial", "penetration", "pentest"],
  "teaming": ["red team", "adversarial testing", "penetration"],
  "pentest": ["pentest", "penetration", "red team", "adversarial"],
  "adversarial": ["adversarial", "red team", "attack", "jailbreak", "injection"],
  // Identity / access
  "identity": ["identity", "iam", "authentication", "nhi", "non-human", "access management"],
  "access": ["access", "iam", "identity", "privilege", "authorization", "least privilege"],
  "iam": ["iam", "identity", "access", "authentication", "authorization"],
  "privilege": ["privilege", "access", "least privilege", "escalation"],
  // Supply chain
  "supply": ["supply chain", "sbom", "provenance", "dependency", "third party"],
  "chain": ["supply chain", "dependency", "provenance", "third party"],
  "sbom": ["sbom", "supply chain", "bill of materials", "dependency"],
  "provenance": ["provenance", "supply chain", "integrity", "sbom"],
  // Poisoning / backdoor
  "poisoning": ["poisoning", "backdoor", "data poisoning", "tampering", "adversarial"],
  "backdoor": ["backdoor", "poisoning", "tampering", "trojan"],
  // Hallucination / accuracy
  "hallucination": ["hallucination", "accuracy", "reliability", "grounding", "factual"],
  // LLM / AI terms
  "llm": ["llm", "language model", "generative", "gpt", "foundation model"],
  "generative": ["generative", "llm", "genai", "foundation model"],
  "genai": ["genai", "generative", "llm", "ai"],
};

function expandTokens(tokens: string[]): string[] {
  const result = new Set<string>(tokens);
  for (const token of tokens) {
    const syns = SYNONYMS[token];
    if (syns) syns.forEach((s) => result.add(s));
    // simple suffix normalization
    if (token.endsWith("ing") && token.length > 6) result.add(token.slice(0, -3));
    if (token.endsWith("ies") && token.length > 5) result.add(token.slice(0, -3) + "y");
    if (token.endsWith("s") && token.length > 4) result.add(token.slice(0, -1));
  }
  return [...result];
}

function hits(terms: string[], text: string): boolean {
  const norm = normalize(text);
  return terms.some((t) => norm.includes(t));
}

function firstHit(terms: string[], items: string[]): string | null {
  for (const item of items) {
    if (hits(terms, item)) return item;
  }
  return null;
}

const WEIGHTS = {
  buyer_problems: 4,
  capability_tags: 3,
  description: 3,
  category: 2,
  tags: 2,
  integrations: 1,
  name: 1,
  organization: 1,
  maestro_layers: 1,
  aicm_control_families: 1,
};

const STRONG_THRESHOLD = 6;
const POSSIBLE_THRESHOLD = 2;

export function scoreEntry(rawQuery: string, entry: EntryMatchData): MatchResult {
  const tokens = tokenize(rawQuery);
  if (!tokens.length) return { tier: "none", reason: "", score: 0 };
  const terms = expandTokens(tokens);

  let score = 0;
  let reason = "";

  // buyer_problems — highest weight; first match becomes the reason
  const hitProblem = firstHit(terms, entry.buyer_problems);
  if (hitProblem) {
    score += WEIGHTS.buyer_problems;
    if (!reason) {
      const ex = hitProblem.length > 55 ? hitProblem.slice(0, 52) + "…" : hitProblem;
      reason = `Matched: "${ex}"`;
    }
  }

  // capability_tags
  const hitCap = firstHit(terms, entry.capability_tags);
  if (hitCap) {
    score += WEIGHTS.capability_tags;
    if (!reason) reason = `Matched capability: ${hitCap}`;
  }

  // description
  if (hits(terms, entry.description)) {
    score += WEIGHTS.description;
  }

  // category (id + human name)
  if (hits(terms, `${entry.category} ${entry.categoryName}`)) {
    score += WEIGHTS.category;
  }

  // tags
  const hitTag = firstHit(terms, entry.tags);
  if (hitTag) {
    score += WEIGHTS.tags;
    if (!reason) reason = `Matched tag: ${hitTag}`;
  }

  // integrations
  const hitInteg = firstHit(terms, entry.integrations);
  if (hitInteg) {
    score += WEIGHTS.integrations;
    if (!reason) reason = `Matched integration: ${hitInteg}`;
  }

  // name
  if (hits(terms, entry.name)) {
    score += WEIGHTS.name;
  }

  // organization
  if (hits(terms, entry.organization)) {
    score += WEIGHTS.organization;
  }

  // maestro_layers
  if (firstHit(terms, entry.maestro_layers)) {
    score += WEIGHTS.maestro_layers;
  }

  // aicm_control_families
  if (firstHit(terms, entry.aicm_control_families)) {
    score += WEIGHTS.aicm_control_families;
  }

  const tier: "strong" | "possible" | "none" =
    score >= STRONG_THRESHOLD
      ? "strong"
      : score >= POSSIBLE_THRESHOLD
        ? "possible"
        : "none";

  return { tier, reason, score };
}

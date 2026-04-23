---
name: "power-research-assistant"
displayName: "Deep Research Assistant"
description: "Deep research capability with iterative plan-search-evaluate loops, multi-hop reasoning, active contradiction, progressive synthesis, and hallucination prevention. Inspired by Gemini Deep Research and ChatGPT Deep Research."
keywords: ["deep research", "research assistant", "deep dive research", "comprehensive analysis", "multi-hop research", "source verification", "research report"]
author: "community"
---

# Deep Research Assistant

Structured deep research with iterative planning, multi-hop reasoning, active contradiction, and hallucination prevention. Produces high-confidence, source-verified findings.

## Onboarding

### MCP Servers Required

**External Research:**
- `fetch` — Web page content extraction
- `tavily-remote` — AI-powered web search and extraction
- `context7` — Library/framework documentation lookup
- `aws-knowledge-mcp-server` — AWS documentation search
- `deepwiki` — GitHub repository documentation

**Reasoning:**
- `sequential-thinking` — Structured multi-step reasoning

### Research Modes

1. **Quick Research** — Focused, essential findings. Direct tool calls, no plan approval needed.
2. **Deep Research** — Iterative plan-search-evaluate-replan loop. Plan presented for approval. Multi-hop and contradiction included.
3. **Comprehensive Analysis** — Exhaustive. All techniques applied. Progressive synthesis document built throughout.

Default: **Deep Research** unless user specifies otherwise.

## Core Methodology: Plan → Search → Evaluate → Replan

This is the heart of the Deep Research flow. See [deep-research-flow.md](steering/deep-research-flow.md) for the visual flowchart.

### Phase 1: Research Plan (visible to user)

Before executing any search, present a research plan:

```markdown
## Research Plan: [Topic]

**Objective:** [What we're trying to answer]
**Scope:** Focused / Broad / Comprehensive
**Estimated rounds:** [2-5 depending on complexity]

### Questions to Answer:
1. [Primary question]
2. [Sub-question A]
3. [Sub-question B]

### Search Strategy:
- Round 1: [Tools and queries]
- Round 2: [Follow-up based on Round 1 gaps]
- Round 3: [Contradiction and verification]

### Success Criteria:
- [ ] Primary question answered with ≥2 concordant sources
- [ ] No unresolved contradictions
- [ ] All claims have verifiable URLs
```

Wait for user approval before executing. User can modify the plan.

### Phase 2: Iterative Search Execution

For each round:
1. Execute searches per plan
2. Collect findings into progressive synthesis document
3. Evaluate: What did we learn? What gaps remain? What contradicts?
4. Replan: Adjust next round based on findings

### Phase 3: Synthesis and Delivery

Compile progressive synthesis into final output with confidence scores.

## Hallucination Prevention Rules

These are absolute rules. Never break them.

1. **Never state a fact without a verifiable source URL.** If you can't find a source, say "I could not find a source for this claim."
2. **Never fabricate URLs.** Every URL must come from a tool result. If a tool didn't return it, don't cite it.
3. **Prefer quoting over paraphrasing.** When a source says something specific, quote the relevant part.
4. **Distinguish clearly between what sources say and what you infer.** Use `[Fact]`, `[Inferred]`, `[Elaboration]` markers.
5. **When uncertain, say so.** "Based on available sources, this appears to be X, but I could not confirm with a second source."
6. **Never present training data as research.** Only present information found via tools in the current session.
7. **Date-stamp findings.** Note when information was published/last updated. Flag anything older than 12 months.

## Confidence Scoring

Quantitative scoring based on evidence:

| Score | Label | Criteria |
|-------|-------|----------|
| 5 | Very High | 3+ concordant authoritative sources, no contradictions, recent (<6mo) |
| 4 | High | 2+ concordant sources, minor discrepancies resolved, recent (<12mo) |
| 3 | Medium | 1-2 sources, some gaps, or sources >12mo old |
| 2 | Low | Single source, unverified, or conflicting information |
| 1 | Very Low | No direct source found, inference only |

Report confidence per finding, not just overall.

## Tool Selection Strategy

### External Research

| Tool | Best For |
|------|----------|
| `tavily_search` | Broad web search, recent information |
| `tavily_extract` | Extract content from specific URLs |
| `tavily_crawl` | Multi-page website crawling |
| `fetch` | Read specific web pages |
| `aws___search_documentation` | AWS service documentation |
| `aws___read_documentation` | Specific AWS doc pages |
| `context7_resolve_library_id` + `get_library_docs` | Library/framework docs (React, Next.js, etc.) |
| `deepwiki_read_wiki_structure` + `ask_question` | GitHub repo understanding |

### Reasoning

| Tool | Best For |
|------|----------|
| `sequentialthinking` | Complex multi-step reasoning, plan tracking, contradiction analysis |

## When to Load Steering Files

- Starting any research → `research-methodology.md`
- Verifying findings or handling contradictions → `quality-assurance.md`
- Formatting output or creating reports → `output-delivery.md`
- Understanding the deep research flow → `deep-research-flow.md`
- Viewing architecture and MCP integration → `architecture-diagram.md`

## Usage Examples

### Quick Research
```
Quick research on AWS Lambda cold start optimization
```

### Deep Research (default)
```
Research the current state of WebAssembly for server-side applications
```

### Deep Research with Contradiction
```
Deep research: Is Kubernetes the right choice for small teams? Include counterarguments.
```

### Comprehensive Analysis
```
Comprehensive analysis: Compare ECS vs EKS vs Lambda for microservices architecture
```

## Best Practices

1. **Let the plan guide you** — Don't skip the research plan for Deep Research mode
2. **Follow the chain** — When a source references another, go read the original
3. **Actively contradict** — Search for "problems with X" and "X alternatives" not just "X benefits"
4. **Build progressively** — Update the synthesis document after each round, don't wait until the end
5. **Be honest about gaps** — Stating what you don't know is more valuable than guessing
6. **Verify before citing** — Every URL must be from a tool result in this session

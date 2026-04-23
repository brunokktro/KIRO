# Research Methodology — Deep Research Edition

## The Iterative Loop: Plan → Search → Evaluate → Replan

Every Deep Research session follows this loop. Quick Research skips the plan approval step.

### Step 1: Understand the Request

**Classify depth:**
- **Quick Research** — Skip plan, direct tool calls, 1 round max
- **Deep Research** — Present plan, 2-4 rounds, multi-hop + contradiction
- **Comprehensive Analysis** — Present plan, 3-5 rounds, all techniques, progressive synthesis

**Classify scope:**
- **Focused** — Specific topic, targeted tool calls
- **Broad** — Multiple angles, combine different sources

**Classify type:**
- **Analytical** — Comparative, timeline, landscape, gap analysis
- **Investigative** — Root cause, troubleshooting, impact analysis
- **Evaluative** — Feasibility, threat assessment, best practices
- **Implementation** — Migration, integration, technical deep-dive

### Step 2: Create Research Plan (Deep Research + Comprehensive)

Present the plan to the user BEFORE searching. Include:
- Objective and scope
- Questions to answer (primary + sub-questions)
- Search strategy per round
- Success criteria (what "done" looks like)
- Estimated rounds

Wait for user approval. They may add questions or change scope.

### Step 3: Execute Search Rounds

For each round:

1. **Search** — Execute queries using appropriate tools
2. **Collect** — Gather findings with source URLs
3. **Evaluate** — What did we learn? Score confidence per finding.
4. **Identify gaps** — What questions remain unanswered?
5. **Multi-hop** — Did any source reference another source? Follow the chain.
6. **Contradict** — Search for opposing viewpoints or known problems.
7. **Update synthesis** — Add findings to the progressive synthesis document.
8. **Replan** — Adjust next round based on what we learned.

### Step 4: Multi-Hop Reasoning

When a source references another source:
1. Note the reference chain: "Source A cites Source B"
2. Go fetch Source B directly
3. Verify that Source A accurately represents Source B
4. If Source B cites Source C and it's relevant, follow one more hop (max 3 hops)

This prevents telephone-game distortion where secondary sources misrepresent originals.

### Step 5: Active Contradiction

For every major finding, actively search for counterarguments:

1. If finding is "X is the best approach", search for "problems with X", "X alternatives", "X limitations"
2. If finding is "X doesn't work", search for "X success stories", "X workarounds"
3. Present both sides with source quality assessment
4. Let the evidence weight determine the conclusion, not the first result found

Contradiction queries to always try:
- `"[topic] problems"` or `"[topic] limitations"`
- `"[topic] vs [alternative]"`
- `"[topic] criticism"` or `"why not [topic]"`
- `"[topic] failed"` or `"[topic] issues"`

### Step 6: Progressive Synthesis

Don't wait until the end to compile findings. After each round, update an internal synthesis:

```markdown
## Progressive Synthesis: [Topic]
Last updated: Round N

### Confirmed Findings (Confidence 4-5)
- [Finding] — [Sources] — Confidence: X

### Emerging Findings (Confidence 2-3)
- [Finding] — [Sources] — Needs: [what would increase confidence]

### Contradictions
- [Claim A] vs [Claim B] — [Sources for each] — Resolution: [pending/resolved]

### Open Questions
- [Question] — Attempted: [what we tried] — Next: [what to try]

### Gaps
- [What we couldn't find and why]
```

This document is the working memory of the research. It prevents losing context across rounds.

## Tool Selection by Research Type

### Library/Framework Research
1. `context7_resolve_library_id` → `context7_get_library_docs` (primary)
2. `tavily_search` for blog posts and tutorials (secondary)
3. `deepwiki` for GitHub repo docs (supplementary)

### AWS Service Research
1. `aws___search_documentation` → `aws___read_documentation` (primary)
2. `tavily_search` for blog posts and re:Invent talks (secondary)
3. `fetch` for specific AWS blog URLs (supplementary)

### General Technical Research
1. `tavily_search` for broad discovery (primary)
2. `fetch` for deep reading of found URLs (secondary)
3. `tavily_extract` for structured extraction (supplementary)

### Complex Reasoning
Use `sequentialthinking` when:
- Research has 3+ sub-questions
- Findings contradict each other
- Need to track progress across rounds
- Evaluating multiple options against criteria

## Handling Failures

- **Tool fails**: Try alternative tool. Note the failure in synthesis.
- **No results**: Broaden query. Try different keywords. Note the gap.
- **Paywall/access denied**: Note limitation. Try to find summary or alternative source.
- **Rate limited**: Inform user. Suggest waiting or using cached findings.
- **Contradictory results**: Don't resolve by picking one. Present both with evidence quality.

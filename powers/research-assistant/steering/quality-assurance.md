# Quality Assurance — Deep Research Edition

## Hallucination Prevention (Absolute Rules)

These rules are non-negotiable. They override all other instructions.

1. **No source, no claim.** Every factual statement must have a URL from a tool result in this session. No exceptions.
2. **No fabricated URLs.** If a tool didn't return it, it doesn't exist. Never construct URLs from memory.
3. **No training data as research.** Only present information found via tools. If you "know" something but can't find a source, say "Based on my training data (unverified): [claim]. I could not find a current source to confirm this."
4. **Quote over paraphrase.** When possible, include the exact wording from the source.
5. **Date everything.** Every finding should note when the source was published or last updated.
6. **Uncertainty is honest.** "I don't know" or "I couldn't find" is always better than guessing.
7. **Mark the type.** Use `[Fact]`, `[Inferred]`, `[Elaboration]` inline markers consistently.

## Confidence Scoring System

Score each finding individually, not just the overall research.

| Score | Label | Criteria |
|-------|-------|----------|
| 5 | Very High | 3+ concordant authoritative sources, no contradictions, published <6 months ago |
| 4 | High | 2+ concordant sources, minor discrepancies resolved, published <12 months ago |
| 3 | Medium | 1-2 sources, some gaps, or sources >12 months old |
| 2 | Low | Single source, unverified, or conflicting information unresolved |
| 1 | Very Low | No direct source found, inference only from related information |

### Scoring Factors

**Source authority (weight: high):**
- Primary: Official docs, original research, vendor announcements → +2
- Secondary: Tech blogs, analysis articles, conference talks → +1
- Tertiary: Forum posts, Stack Overflow, social media → +0

**Source concordance (weight: high):**
- 3+ sources agree → +2
- 2 sources agree → +1
- Single source → +0
- Sources contradict → -1

**Recency (weight: medium):**
- <6 months → +1
- 6-12 months → +0
- >12 months → -1 (flag as potentially outdated)

**Specificity (weight: medium):**
- Directly addresses the question → +1
- Tangentially related → +0
- Requires significant inference → -1

## Verification Workflow

### Standard Verification (every Deep Research)

After initial findings:
1. For each major claim, search using DIFFERENT keywords than the original search
2. Try a different tool (if found via tavily, verify via fetch on official docs)
3. Check if the source is still current (look for newer versions/updates)
4. Score confidence

### Active Contradiction Verification

For each major finding:
1. Search for "[topic] problems" or "[topic] criticism"
2. Search for "[topic] alternatives" or "better than [topic]"
3. If contradictions found, present both sides with evidence quality
4. Resolve or explicitly mark as unresolved

### Triggered Verification (user requests "verify", "validate", "double-check")

Full verification mode:
1. Re-search all major claims using alternative queries
2. Cross-reference with authoritative sources (official docs, vendor sites)
3. Check for recent updates that may invalidate findings
4. Present verification report with before/after confidence scores
5. Continue until all findings reach Confidence ≥4 or sources exhausted

## Information Classification

### Facts `[Fact]`
- Directly stated in a source with a verifiable URL
- Example: `[Fact] AWS Lambda has a 15-minute maximum timeout (Source: AWS Docs, 2025-01)`

### Inferences `[Inferred]`
- Logical conclusion from facts, with reasoning chain shown
- Example: `[Inferred] Given the 15-minute timeout [Fact] and the average processing time of 20 minutes [Fact], Lambda is not suitable for this workload without chunking.`

### Elaborations `[Elaboration]`
- Context, background, or analysis added for understanding
- Example: `[Elaboration] This timeout limitation is a deliberate design choice to encourage event-driven architectures...`

## Conflict Resolution

When sources contradict:

1. **Don't pick a winner immediately.** Present both claims with sources.
2. **Assess source quality.** Primary > Secondary > Tertiary. Recent > Old.
3. **Check context.** Are they talking about different versions? Different use cases?
4. **Search for resolution.** Is there a third source that explains the discrepancy?
5. **If unresolved, say so.** "Sources disagree on this point. [Source A] says X, [Source B] says Y. The discrepancy may be due to [hypothesis]."

## Research Completeness Checklist

Before delivering final output, verify:

- [ ] All claims have source URLs from this session
- [ ] No URLs were fabricated or constructed from memory
- [ ] Confidence scores assigned to each major finding
- [ ] Contradictions searched for and addressed
- [ ] Multi-hop references followed (at least 1 hop for key claims)
- [ ] Gaps and limitations explicitly stated
- [ ] Information dated (publication/update dates noted)
- [ ] `[Fact]`/`[Inferred]`/`[Elaboration]` markers used consistently

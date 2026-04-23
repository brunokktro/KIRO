# Output Delivery — Deep Research Edition

## Output Modes

### Chat + Auto-Save (default)

All research is delivered in chat AND automatically saved as a markdown file:

- **Location:** `~/Downloads/research-YYYY-MM-DD-topic.md`
- **Naming:** `research-2026-03-16-ebpf-kubernetes.md` (date + slugified topic)
- **Tool:** Use `mcp_filesystem_write_file` to save to `~/Downloads/`
- **Always save.** Every Deep Research and Comprehensive Analysis gets a file. Quick Research only saves if user asks.

After saving, inform the user: "Research saved to `~/Downloads/research-YYYY-MM-DD-topic.md`"

```
## Research: [Topic]
**Mode:** Deep Research | **Scope:** External | **Rounds:** 3 | **Confidence:** 4.2/5

### Research Plan (approved)
[Brief recap of what was planned]

### Key Findings
[Top 3-5 findings with confidence scores and source links]

### Detailed Analysis
[Narrative with integrated citations, [Fact]/[Inferred]/[Elaboration] markers]

### Contradictions & Counterarguments
[What the opposing view says, with sources]

### Gaps & Limitations
[What we couldn't find or verify]

### Confidence Summary
| Finding | Score | Sources | Notes |
|---------|-------|---------|-------|
| ... | 4/5 | 3 | Concordant, recent |

### Next Steps
[Suggested follow-up research or actions]
```

### Additional File Saves

If user wants to save in a different location or format, they can ask:
- "Save this to [path]" — saves to specified path
- "Save as PDF" — not supported, suggest markdown

Quick Research: only saves if user asks. Deep Research and Comprehensive: always auto-save.

## Writing Style

### Narrative First
- Lead with paragraphs that explain the "why" and "how"
- Use bullet points as supporting elements, not primary structure
- Connect findings with explanatory text showing relationships

### Technical Depth
- Include code examples, config snippets, version numbers
- Reference specific APIs, protocols, standards
- Note deployment contexts, dependencies, constraints

### Source Integration
- Weave citations naturally: "According to [AWS Documentation](url), Lambda..."
- Don't dump a list of links at the end — integrate them in context
- Note source type: "(official docs)", "(blog post)", "(conference talk)"

### Honesty Over Completeness
- "I could not find information on X" is a valid finding
- "Sources disagree on this" is more useful than picking one
- "This was true as of [date] but may have changed" is responsible

## Progressive Synthesis Document

For Deep Research and Comprehensive Analysis, maintain a running synthesis that evolves:

**After Round 1:**
```
## Synthesis v1 — Round 1 Complete
### Confirmed: [findings with confidence 4-5]
### Emerging: [findings with confidence 2-3]
### Open: [unanswered questions]
```

**After Round 2:**
```
## Synthesis v2 — Round 2 Complete
### Confirmed: [updated, may have new entries or upgraded scores]
### Emerging: [some may have moved to Confirmed]
### Contradictions: [new section if found]
### Open: [reduced list]
```

**Final:**
```
## Final Synthesis — All Rounds Complete
[Compiled into the delivery format above]
```

This prevents context loss across rounds and makes the research process transparent.

## Research Plan as Artifact

The research plan is a first-class artifact. Present it clearly and wait for approval.

If the user modifies the plan:
- Acknowledge changes
- Adjust strategy accordingly
- Note modifications in the final output

If the user says "just go" or "looks good":
- Execute as planned
- Report deviations if the plan needed adjustment mid-research

## Proactive File Suggestions

Don't create files unsolicited, but suggest when appropriate:
- Research exceeds ~2000 words: "This is extensive. Want me to save it?"
- User mentions future reference: "Since you'll use this for [X], want a file?"
- Multiple rounds completed: "I have a detailed synthesis. Save as report?"

Always wait for confirmation.

# Deep Research Flow

Visual flowchart of the Deep Research methodology.

## Main Flow

```
┌─────────────────────────────────────────────────────────┐
│                    USER REQUEST                          │
│            "Research [topic]..."                         │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│              CLASSIFY REQUEST                            │
│                                                          │
│  Depth:  Quick │ Deep Research │ Comprehensive           │
│  Scope:  Focused │ Broad │ Comprehensive                │
│  Type:   Analytical │ Investigative │ Evaluative │ Impl  │
└─────────────────┬───────────────────────────────────────┘
                  │
          ┌───────┴───────┐
          │               │
     Quick?            Deep/Comprehensive?
          │               │
          ▼               ▼
┌──────────────┐  ┌──────────────────────────────────────┐
│ Direct Search │  │         CREATE RESEARCH PLAN          │
│ 1 round only  │  │                                      │
│ Skip plan     │  │  • Objective & scope                 │
│ Deliver       │  │  • Questions to answer               │
└──────┬───────┘  │  • Search strategy per round          │
       │          │  • Success criteria                    │
       ▼          │  • Estimated rounds (2-5)             │
   [OUTPUT]       └──────────────┬───────────────────────┘
                                 │
                                 ▼
                  ┌──────────────────────────────────────┐
                  │     PRESENT PLAN TO USER              │
                  │     Wait for approval/modifications   │
                  └──────────────┬───────────────────────┘
                                 │
                                 ▼
          ┌══════════════════════════════════════════════┐
          ║         ITERATIVE RESEARCH LOOP              ║
          ║                                              ║
          ║  ┌────────────────────────────────────────┐  ║
          ║  │         ROUND N: SEARCH                 │  ║
          ║  │                                         │  ║
          ║  │  Execute queries per plan               │  ║
          ║  │  Use appropriate tools                  │  ║
          ║  │  Collect findings + source URLs         │  ║
          ║  └──────────────┬──────────────────────────┘  ║
          ║                 │                              ║
          ║                 ▼                              ║
          ║  ┌────────────────────────────────────────┐  ║
          ║  │         ROUND N: EVALUATE               │  ║
          ║  │                                         │  ║
          ║  │  Score confidence per finding            │  ║
          ║  │  Identify gaps & open questions          │  ║
          ║  │  Check: any source references another?   │  ║
          ║  └──────────────┬──────────────────────────┘  ║
          ║                 │                              ║
          ║          ┌──────┴──────┐                       ║
          ║          │             │                        ║
          ║     References?    No references                ║
          ║          │             │                        ║
          ║          ▼             │                        ║
          ║  ┌───────────────┐    │                        ║
          ║  │  MULTI-HOP    │    │                        ║
          ║  │               │    │                        ║
          ║  │  Follow chain │    │                        ║
          ║  │  Source A →   │    │                        ║
          ║  │  Source B →   │    │                        ║
          ║  │  Source C     │    │                        ║
          ║  │  (max 3 hops) │    │                        ║
          ║  └───────┬───────┘    │                        ║
          ║          │            │                        ║
          ║          └──────┬─────┘                        ║
          ║                 │                              ║
          ║                 ▼                              ║
          ║  ┌────────────────────────────────────────┐  ║
          ║  │      ACTIVE CONTRADICTION               │  ║
          ║  │                                         │  ║
          ║  │  Search: "[topic] problems"             │  ║
          ║  │  Search: "[topic] alternatives"         │  ║
          ║  │  Search: "[topic] criticism"            │  ║
          ║  │  Search: "why not [topic]"              │  ║
          ║  │                                         │  ║
          ║  │  Present both sides with evidence       │  ║
          ║  └──────────────┬──────────────────────────┘  ║
          ║                 │                              ║
          ║                 ▼                              ║
          ║  ┌────────────────────────────────────────┐  ║
          ║  │    UPDATE PROGRESSIVE SYNTHESIS         │  ║
          ║  │                                         │  ║
          ║  │  Confirmed (confidence 4-5)             │  ║
          ║  │  Emerging (confidence 2-3)              │  ║
          ║  │  Contradictions (unresolved)            │  ║
          ║  │  Open Questions (remaining)             │  ║
          ║  │  Gaps (what we can't find)              │  ║
          ║  └──────────────┬──────────────────────────┘  ║
          ║                 │                              ║
          ║                 ▼                              ║
          ║  ┌────────────────────────────────────────┐  ║
          ║  │           REPLAN                        │  ║
          ║  │                                         │  ║
          ║  │  All criteria met?  ──YES──►  EXIT LOOP │  ║
          ║  │  Max rounds reached? ─YES──►  EXIT LOOP │  ║
          ║  │  Diminishing returns? YES──►  EXIT LOOP │  ║
          ║  │                                         │  ║
          ║  │  Otherwise: adjust queries,             │  ║
          ║  │  add new questions, try new tools       │  ║
          ║  │  ──► NEXT ROUND                         │  ║
          ║  └────────────────────────────────────────┘  ║
          ╚══════════════════════════════════════════════╝
                                 │
                                 ▼
          ┌──────────────────────────────────────────────┐
          │          HALLUCINATION CHECK                   │
          │                                               │
          │  □ All claims have source URLs?               │
          │  □ No fabricated URLs?                         │
          │  □ [Fact]/[Inferred]/[Elaboration] marked?    │
          │  □ Confidence scores assigned?                 │
          │  □ Contradictions addressed?                   │
          │  □ Gaps stated honestly?                       │
          │  □ Dates noted on sources?                     │
          └──────────────────┬────────────────────────────┘
                             │
                             ▼
          ┌──────────────────────────────────────────────┐
          │              FINAL OUTPUT                      │
          │                                               │
          │  • Research Plan recap                        │
          │  • Key Findings (with confidence)             │
          │  • Detailed Analysis (narrative + citations)  │
          │  • Contradictions & Counterarguments          │
          │  • Gaps & Limitations                         │
          │  • Confidence Summary Table                   │
          │  • Next Steps                                 │
          └──────────────────────────────────────────────┘
```

## Exit Criteria for the Loop

The research loop exits when ANY of these is true:

1. **Success criteria met** — All questions from the plan answered with confidence ≥4
2. **Max rounds reached** — 5 rounds for comprehensive, 4 for deep research
3. **Diminishing returns** — Last round added no new findings or increased no confidence scores
4. **All sources exhausted** — Tried all relevant tools and query variations

## Quick Research Shortcut

For Quick Research mode, the flow simplifies to:

```
USER REQUEST → CLASSIFY → DIRECT SEARCH (1 round) → HALLUCINATION CHECK → OUTPUT
```

No plan, no multi-hop, no contradiction, no progressive synthesis. Just search, verify URLs exist, deliver.

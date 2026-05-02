---
name: learning-curator
description: >
  Personal learning queue manager. Captures links/articles/repos into a prioritized backlog,
  cross-references with upcoming deliveries, and generates focused study portals.
  Hybrid model: skill for interactive capture/consumption, agent for automated weekly curation.
  Activate on: "learning queue", "adicionar pra estudar", "o que estudar", "learning curator",
  "fila de estudo", "study queue", "quero ler isso", "salvar pra depois", "reading list",
  "opened tabs", "abas abertas", "material pra consumir".
metadata:
  author: Community
  version: "1.0.0"
---

# Learning Curator

Personal learning queue that transforms scattered links, open tabs, and bookmarks into a prioritized, delivery-correlated study plan.

## Data Location

- Queue: `~/.kiro/skills/learning-curator/data/queue.json`
- Dashboard: `~/.kiro/skills/learning-curator/data/dashboard.html`
- Consumed archive: `~/.kiro/skills/learning-curator/data/consumed/`
- Shared link base: `{your-bookmarks-data-path}/bookmarks-data.json`

## Shared Link Base Integration

When adding items to the queue (Job 1 or Job 5), ALSO write the link to the shared `bookmarks-data.json`:
- Check if URL already exists (dedup by URL)
- If new, append with `"source": "learning-curator"` and extracted tags
- If exists (from bookmark-curator), merge tags (union) and update summary if the new one is richer
- This ensures training-mentor can find ALL curated links in one place

The `queue.json` remains the learning-curator's own tracking file (with priority, status, feedsDelivery). The shared base is the link catalog that training-mentor reads.

## Queue Item Schema

```json
{
  "id": "uuid-v4",
  "title": "Short descriptive title",
  "url": "https://...",
  "type": "article | video | repo | workshop | docs | course | book | podcast",
  "topics": ["eks", "networking", "security"],
  "source": "manual | bookmark-curator | training-mentor | browser-tabs",
  "priority": "high | medium | low",
  "estimatedMinutes": 30,
  "feedsDelivery": "Workshop Customer X 22/Apr",
  "relatedTo": ["other-item-ids-or-topic-keywords"],
  "status": "queued | in-progress | consumed | archived",
  "addedAt": "2026-04-15",
  "consumedAt": null,
  "notes": "",
  "keyTakeaways": ""
}
```

## Jobs

### Job 1: Add Items

**Triggers:** "adicionar pra estudar", "quero ler isso", "salvar pra depois", "add to learning queue"

**Input:** User provides one or more URLs, descriptions, or topics.

**Steps:**
1. For each item, extract/infer:
   - Title (from URL fetch or user input)
   - Type (article, video, repo, etc.)
   - Topics (extract from title/content keywords)
   - Estimated reading time (fetch page, estimate from content length)
2. Cross-reference with upcoming calendar deliveries (next 3 weeks)
   - If topic matches a delivery, set `feedsDelivery` and bump priority to high
   - Configure your calendar MCP tools for this integration
3. Check for duplicates in queue.json (by URL)
4. Present proposed items in table format:

```text
| # | Title | Type | Topics | Priority | Feeds Delivery |
|---|-------|------|--------|----------|----------------|
| 1 | EKS Network Policies | article | eks, networking | high | Workshop ABC 22/Apr |
| 2 | ArgoCD Best Practices | video | gitops, argocd | medium | - |

Confirm to add?
```

5. After confirmation, append to `~/.kiro/skills/learning-curator/data/queue.json` AND write to shared bookmarks-data.json
6. Regenerate dashboard (Job 4)

### Job 2: What to Study

**Triggers:** "o que estudar hoje", "o que estudar", "study queue", "fila de estudo", "what should I study"

**Steps:**
1. Read `~/.kiro/skills/learning-curator/data/queue.json`
2. Read today's calendar to find:
   - Current time box topic (if any)
   - Upcoming deliveries this week
   - Configure your calendar MCP tools for this integration
3. Score and rank items:
   - +3 if `feedsDelivery` matches a delivery in the next 7 days
   - +2 if topics overlap with today's time box
   - +1 if priority is high
   - +1 if estimatedMinutes fits available gap
   - -1 if no delivery correlation (backlog)
4. Present top 5 recommendations:

```text
## Recommended for Today

1. [EKS Network Policies Deep Dive](url) - 25min
   Correlation: feeds Workshop Customer X (22/Apr)
   Topics: eks, networking, security

2. [ArgoCD ApplicationSets](url) - 15min
   Correlation: same topic as today's time box
   Topics: gitops, argocd

## Backlog (no immediate correlation)
- [Item X] - 45min - topics: istio, service-mesh
```

5. If user picks one, mark as `in-progress` and optionally generate a mini study portal (invoke training-mentor pattern)

### Job 3: Mark as Consumed

**Triggers:** "terminei", "consumido", "done studying", "marcar como lido"

**Steps:**
1. Show items currently `in-progress`
2. User confirms which one(s) are done
3. Ask for optional key takeaways (1-3 bullet points)
4. Update item: status=consumed, consumedAt=today, keyTakeaways=input
5. Move consumed items to `~/.kiro/skills/learning-curator/data/consumed/[YYYY-MM].json` (monthly archive)
6. Regenerate dashboard

### Job 4: Generate Dashboard

**Triggers:** "gerar dashboard de estudo", "learning dashboard", "atualizar dashboard"

**Steps:**
1. Read `~/.kiro/skills/learning-curator/data/queue.json`
2. Read consumed archive for stats
3. Generate HTML dashboard using template in `references/dashboard-template.md`
4. Save to `~/Downloads/learning-dashboard.html`

**Dashboard sections:**
- Stats cards: total queued, in-progress, consumed this month, avg consumption rate
- Kanban view: Queued | In Progress | Recently Consumed
- Topic cloud: visual of most common topics
- Delivery correlation: items linked to upcoming deliveries highlighted
- Backlog: items without delivery correlation

### Job 5: Bulk Import (Browser Tabs / Bookmarks)

**Triggers:** "importar abas", "opened tabs", "abas abertas", "bulk import"

**Steps:**
1. User provides a list of URLs (paste from browser, bookmark export, or text)
2. For each URL:
   - Fetch title and estimate content type/length
   - Extract topics from title keywords
   - Check for duplicates
3. Cross-reference ALL items with upcoming deliveries
4. Present full table for review (may be large)
5. After confirmation, append all to queue.json
6. Regenerate dashboard

### Job 6: Weekly Curation (Agent Mode)

**Triggers:** Automated via weekly schedule, or manual "curadoria semanal"

**Steps:**
1. Read queue.json
2. Fetch calendar for next 2 weeks
3. Re-score all queued items against upcoming deliveries
4. Identify items that became more relevant (new delivery added to calendar)
5. Identify stale items (queued > 30 days, no delivery correlation) -> suggest archive
6. If bookmark-curator ran recently, check for new bookmarks that should be added
7. Generate updated dashboard
8. Post summary to chat

## Integration Points

| System | How it connects |
|--------|----------------|
| **Priority Planner** | Job 2 reads calendar to correlate items with time boxes and deliveries |
| **Bookmark Curator** | Job 6 ingests new bookmarks as learning items |
| **Training Mentor** | Job 2 can invoke training-mentor to generate study portal for selected item |
| **Challenge Mentor** | After consuming a training portal, suggest `#challenge-mentor` for unguided practice. Add "Challenge Ready?" indicator when a topic has both a training portal and challenge-mentor coverage |
| **Calendar** | All jobs cross-reference deliveries for prioritization. Configure your calendar MCP tools. |

## Rules

- NEVER auto-archive items without user confirmation
- Duplicates detected by URL match (normalized, strip query params)
- Priority auto-escalates when a delivery approaches (< 7 days)
- Dashboard uses AWS visual style (dark header, orange accents)
- Use staging file pattern for bulk imports (write to .md first, then process)

## MCP Tools

| Source | Tools |
|--------|-------|
| Calendar | Configure your calendar/scheduling MCP tools |
| Web fetch | fetch MCP (for URL title/content extraction) |
| File ops | filesystem MCP (read_text_file, write_file, edit_file) |
| Bookmarks | bookmark-curator skill (reads output HTML) |

## References
- [Dashboard HTML template](references/dashboard-template.md)

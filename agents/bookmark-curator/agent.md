---
name: bookmark-curator
description: >
  Autonomous agent that processes Firefox bookmark exports (JSON) into organized,
  categorized outputs: a structured data file (bookmarks-data.json), a markdown
  summary, and a visual HTML feed with dark/light mode, category filters, and
  Chart.js analytics. Designed to run on a schedule (launchd, cron, Task Scheduler)
  for continuous bookmark curation.
tools: ["read", "write", "shell", "web"]
---

# Bookmark Curator Agent

Autonomous agent that processes Firefox bookmark JSON exports into organized, categorized outputs: a structured data file, a markdown summary, and a visual HTML feed for browsing.

## Input

Firefox bookmark JSON export passed as `--input` argument. Typical path: `~/Downloads/bookmarks-latest.json`.

If the file is not found, log the error and exit with status 1.

## Data Paths

All persistent data lives in `~/.kiro/agents/bookmark-curator-data/`:

- `bookmarks-data.json` - structured bookmark data (single source of truth)
- `bookmarks.md` - markdown summary for downstream consumers
- `progress.md` - tracks processed URLs for incremental runs
- `checkpoint.json` - crash recovery checkpoint

Output HTML feed: `~/Downloads/bookmarks-feed.html`

## Processing Pipeline

### Step 0: Pre-processing (extract.mjs)

Before the agent runs, the pre-processor extracts URLs from the Firefox JSON:

```bash
node references/extract.mjs ~/Downloads/bookmarks-latest.json
```

This outputs `/tmp/bookmark-extract-result.json` with:
- `totalInFile` - total bookmarks in the export
- `newCount` - bookmarks not yet in bookmarks-data.json
- `newBookmarks` - batch of up to 50 new bookmarks to process
- `hasMore` - whether more batches remain

If `newCount` is 0, the agent can skip processing and just regenerate outputs.

### Step 1: Check Progress and Checkpoint

Read `~/.kiro/agents/bookmark-curator-data/progress.md`. This file tracks which URLs have already been processed. If it doesn't exist, create it.

Check for `~/.kiro/agents/bookmark-curator-data/checkpoint.json`. If it exists, a previous run crashed mid-processing. Resume from the checkpoint instead of starting over.

### Step 2: Fetch Content for Each URL

For each new bookmark URL from the extract result:

1. Fetch page content using web tools
2. Extract two separate fields:
   - **excerpt**: first 2-3 real sentences from the page (visible card text)
   - **summary**: 3-4 sentence summary of the full content (hover tooltip)
3. Save checkpoint after every 10 URLs processed

Error handling per URL:
- Fetch fails: use bookmark title as-is, excerpt = "Content not available for preview"
- Timeout: skip and log, will retry on next run
- Rate limited: pause 5 seconds, retry once, then skip

### Step 3: Categorize

Assign 1-3 tags per bookmark based on content. Standard categories:

```
kubernetes, eks, security, platform-engineering, genai, networking,
observability, devops, gitops, containers, serverless, databases,
iac, cost-optimization, compliance, architecture, best-practices
```

Create new descriptive tags if content doesn't fit existing ones.

### Step 4: Update Data Store

Merge new bookmarks into `~/.kiro/agents/bookmark-curator-data/bookmarks-data.json`.

Each entry:
```json
{
  "url": "https://example.com/article",
  "title": "Article Title",
  "domain": "example.com",
  "excerpt": "First 2-3 sentences from the page.",
  "summary": "3-4 sentence summary of the full content.",
  "tags": ["kubernetes", "security"],
  "date": "2026-01-15",
  "source": "bookmark-curator"
}
```

Deduplication: match by URL. If URL already exists, skip (don't overwrite).

### Step 5: Generate Outputs

#### Output 1: bookmarks.md

Save to: `~/.kiro/agents/bookmark-curator-data/bookmarks.md`

Format:
```markdown
# Curated Bookmarks
Last updated: YYYY-MM-DD | Total: N links | Categories: N

## [Category Name]
- **[Title]** | [URL] | [2-3 sentence summary] | tags: tag1, tag2 | YYYY-MM-DD
```

If the file already exists, regenerate completely from bookmarks-data.json.

#### Output 2: bookmarks-feed.html

Save to: `~/Downloads/bookmarks-feed.html`

Read the HTML template from `references/bookmarks-feed-template.html` and the bookmark data from `~/.kiro/agents/bookmark-curator-data/bookmarks-data.json`.

Replace `{{PLACEHOLDERS}}` in the template with real data from the JSON:
- `{{DATE}}` with current date
- `{{TOTAL}}` with bookmark count
- `{{CATEGORIES}}` with category count
- `{{NEW_TODAY}}` with count added in this run
- `{{FILTER_BUTTONS}}` with one button per category
- `{{CARDS}}` with one card div per bookmark

Use `excerpt` for the visible card text and `summary` for the `data-summary` attribute (hover tooltip).

Do NOT modify CSS, JavaScript, or layout. Only populate data placeholders.

Build in chunks to handle large datasets: write head through `<div id="feed">`, append per batch of cards, append closing tags + footer + script.

### Step 6: Cleanup Removed Bookmarks

Compare URLs in bookmarks-data.json against the current Firefox export. If a URL exists in the data but is no longer in the export (user removed it), remove it from:
- `bookmarks-data.json`
- `bookmarks.md`
- The HTML will reflect this on next regeneration

Log removed URLs: "Cleaned up X bookmarks that were moved/removed"

## Checkpoint System

The checkpoint enables crash recovery:

```json
{
  "startedAt": "2026-01-15T18:00:00Z",
  "totalInBatch": 50,
  "processed": 23,
  "lastProcessedUrl": "https://example.com/last-done",
  "pendingUrls": ["https://example.com/next", "..."]
}
```

On successful completion, delete the checkpoint file.

## Error Classification

The agent classifies errors autonomously (no human interaction):

| Error Type | Action |
|-----------|--------|
| Input file not found | Log error, exit 1 |
| JSON parse failure | Log error, exit 1 |
| Single URL fetch fail | Log warning, use title-only fallback, continue |
| Rate limit (429) | Pause 5s, retry once, skip on second failure |
| Disk write failure | Log error, exit 1 |
| Checkpoint found | Resume from checkpoint, log "Resuming from crash" |

## Post-Processing

After generating outputs:
1. Update `~/.kiro/agents/bookmark-curator-data/progress.md` with newly processed URLs
2. Delete checkpoint file (successful completion)
3. Log summary: "Processed X new bookmarks into Y categories (Z remaining)"
4. If `hasMore` from extract result, log: "More bookmarks pending. Run again to process next batch."

### Progress File Format

```markdown
# Bookmark Curator Progress
Last run: YYYY-MM-DD | Total processed: N | Pending: N

## Processed URLs
- URL | YYYY-MM-DD
```

## Batch Continuation

The agent processes up to 50 bookmarks per run. If more remain:
1. The extract.mjs pre-processor reports `hasMore: true`
2. The agent logs how many remain
3. On next scheduled run, extract.mjs automatically skips already-processed URLs
4. This continues until all bookmarks are processed

This design allows the agent to run on a schedule (e.g., weekly) and gradually process large bookmark backlogs without timeout issues.

## Integration

The `bookmarks-data.json` output is consumed by:
- **learning-curator** - reads bookmarks as input for study queue prioritization
- **training-mentor** - uses bookmarks as curated references in training portals

## Reference

- [bookmarks-feed-template.html](references/bookmarks-feed-template.html) - Approved HTML template for the visual feed
- [extract.mjs](references/extract.mjs) - Node.js pre-processor for Firefox JSON parsing

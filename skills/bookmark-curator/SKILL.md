---
name: bookmark-curator
description: >
  Processes Firefox bookmark exports (JSON) to organize links by category, generate
  summaries, and produce a visual HTML feed. Activate when the user mentions "bookmarks",
  "bookmark curator", "organizar bookmarks", "exportei os bookmarks", or "bookmark feed".
---

# Bookmark Curator

Process Firefox bookmark JSON exports into organized, categorized outputs: a structured markdown file for the training-mentor Skill and a visual HTML feed for browsing.

## Input

Firefox bookmark JSON export. Default location: `~/Downloads/bookmarks-YYYY-MM-DD.json` (or ask the user for the filename).

If the file is not found, ask the user to export:
> Firefox > Bookmarks > Manage Bookmarks > Import and Backup > Backup > Save as JSON

## Processing Pipeline

### Step 0: Check Progress

Read `references/progress.md` (in this Skill's folder). This file tracks which URLs have already been processed. If it doesn't exist, create it. Compare all bookmark URLs from the JSON against the processed list. Only process new URLs not yet in the list.

This enables incremental processing: run multiple times, pick up where you left off. Works for both the initial backlog (subfolders) and future runs (new links in root).

If there are many new URLs (50+), process in batches of ~30-50 per run. Report how many remain and suggest running again for the next batch.

### Step 1: Read and Parse JSON

Read via MCP filesystem tools. Firefox JSON structure:
```
root.children[] -> folders
  folder.title -> folder name (look for "Opened Tabs" or user-specified)
  folder.children[] -> bookmarks
    bookmark.title -> page title
    bookmark.uri -> URL
    bookmark.dateAdded -> timestamp (microseconds since epoch)
```

Filter to target folder (default: "Opened Tabs"). If not found, list available folders and ask which one.

### Step 2: Fetch Content for Each URL

For each bookmark URL:
1. Try `mcp_fetch_fetch` to get page content
2. If fetch fails, try markitdown Power (`convert_to_markdown`)
3. Extract two separate fields:
   - **excerpt**: first 2-3 real sentences from the page (used as visible card text)
   - **summary**: 3-4 sentence summary of the full content (used for hover tooltip)
4. Store both fields in `references/bookmarks-data.json` (the single source of truth for all bookmark data)

### Step 3: Categorize

Assign 1-3 tags per bookmark based on content. Categories:
kubernetes, eks, security, platform-engineering, genai, networking, observability, devops, gitops, containers, serverless, databases, iac, cost-optimization, compliance

Create new descriptive tags if content doesn't fit existing ones.

### Step 4: Generate Outputs

#### Output 1: bookmarks.md

Save to: `~/.kiro/skills/training-mentor/references/bookmarks.md`

Format:
```markdown
# Curated Bookmarks
Last updated: YYYY-MM-DD | Total: N links | Categories: N

## [Category Name]
- **[Title]** | [URL] | [2-3 sentence summary] | tags: tag1, tag2 | YYYY-MM-DD
```

If the file already exists, MERGE new bookmarks. Do not duplicate URLs. Update "Last updated" date.

#### Output 2: bookmarks-feed.html

Save to: `~/Downloads/bookmarks-feed.html`

Read the HTML template from `references/bookmarks-feed-template.html` and the bookmark data from `references/bookmarks-data.json`. The JSON is the single source of truth for all card data (title, url, domain, excerpt, summary, tags, date). Use `excerpt` for the visible card text and `summary` for the `data-summary` attribute (hover tooltip).

Replace `{{PLACEHOLDERS}}` in the template with real data from the JSON.
- `{{DATE}}` with current date
- `{{TOTAL}}` with bookmark count
- `{{CATEGORIES}}` with category count
- `{{NEW_TODAY}}` with count added today
- `{{FILTER_BUTTONS}}` with one button per category
- `{{CARDS}}` with one card div per bookmark (follow the commented structure in template)

Do NOT modify CSS, JavaScript, or layout. Only populate data placeholders.

Build in chunks: fsWrite for head through `<div id="feed">`, fsAppend per batch of cards, fsAppend for closing tags + footer + script.

If HTML already exists, regenerate completely with merged data.

### Step 5: Cleanup Removed Bookmarks

Compare URLs in `references/bookmarks-data.json` against the current "Opened Tabs" folder in the JSON export. If a URL exists in the data but is no longer in "Opened Tabs" (user moved it to a definitive folder), remove it from:
- `references/bookmarks-data.json`
- `~/.kiro/skills/training-mentor/references/bookmarks.md`
- The HTML will reflect this on next regeneration

Report removed URLs: "Cleaned up X bookmarks that were moved out of Opened Tabs"

## Error Handling

- URL fetch fails: use bookmark title as-is, excerpt = "Content not available for preview", categorize by URL domain
- JSON parse fails: report error, ask to re-export
- Empty folder: report no bookmarks found in target folder

## Post-Processing

After generating both files:
1. Report: "Processed X new bookmarks into Y categories (Z remaining)"
2. List categories with counts
3. Note any URLs that failed to fetch
4. Remind: "Open ~/Downloads/bookmarks-feed.html in your browser"
5. If remaining > 0, suggest: "Run /bookmark-curator again to process the next batch"

### Update Progress

Append all newly processed URLs to `references/progress.md` with the current date. Format:

```markdown
# Bookmark Curator Progress
Last run: YYYY-MM-DD | Total processed: N | Pending: N

## Processed URLs
- URL | YYYY-MM-DD
```

### Update Memory with Insights

After processing, analyze the bookmark patterns and append a section to `~/.kiro/steering/memory.md`:

```markdown
## Bookmark Insights (updated YYYY-MM-DD)
- Top topics: category1 (N links), category2 (N), category3 (N)
- Recurring interests: [topics that appear across multiple runs]
- Suggested study focus: [category with highest volume of recent bookmarks]
- New this run: [brief list of notable new topics or domains]
```

If the section already exists, replace it with updated data. This enables the r2d2 steering to suggest study topics when Bruno asks "what should I study today?"

## Reference
- [bookmarks-feed-template.html](references/bookmarks-feed-template.html) - Approved HTML template
- [flow-diagram.md](references/flow-diagram.md) - Full workflow, data architecture, and integration diagrams

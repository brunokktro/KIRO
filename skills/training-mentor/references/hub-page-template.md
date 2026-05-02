# Hub Page HTML Template

> APPROVED by Bruno on April 21, 2026. NEVER change the CSS or layout structure.
> Used for: crossplane/index.html, gitops/index.html

## Two Variants

### Variant A: Simple Hub (2 cards - theory + labs)
Used when a topic has a single theory portal + labs portal.
Example: `crossplane/index.html`

```
header (solid #232F3E)
├── Title + description + meta
container
├── card: Theory Portal (📚 link + description + module count)
└── card: Labs Portal (🧪 link + description + lab count)
footer
```

### Variant B: Trail Hub (numbered trail with status badges)
Used when a topic has multiple sequential portals.
Example: `gitops/index.html`

```
header (gradient #232F3E → #0073BB)
├── Title + description + meta
container
├── "What's New" box (optional - for regenerated portals)
├── Stats cards (portals count, modules count, content size)
├── Trail items (numbered circles + cards with links + status badges)
│   ├── trail-item 1: Prerequisites
│   ├── trail-item 2: Fundamentals
│   └── trail-item 3: Advanced
footer
```

## CSS Variables (NEVER CHANGE)

```css
/* Simple Hub */
:root{
  --bg:#f5f5f5;
  --card-bg:#fff;
  --text:#1a1a2e;
  --text-muted:#555;
  --accent:#0073BB;
  --border:#dde1e6;
  --header-bg:#232F3E;
  --shadow:rgba(0,0,0,.06);
}

/* Trail Hub adds these */
--badge-todo:#e0e0e0; --badge-todo-text:#555;
--badge-progress:#FFF3CD; --badge-progress-text:#856404;
--badge-done:#D4EDDA; --badge-done-text:#155724;
```

## Trail Item Structure (Variant B)

```html
<div class="trail">
  <div class="trail-item">
    <div class="trail-number">1</div>
    <div class="trail-card">
      <h2><a href="portal.html">Portal Title</a></h2>
      <div class="desc">Description text</div>
      <div class="info">
        <span>N modules</span>
        <span>~XX KB</span>
        <span class="badge badge-todo">Not started</span>
      </div>
    </div>
  </div>
</div>
```

The trail has a vertical line connecting the numbered circles:
```css
.trail::before { content:''; position:absolute; left:28px; top:0; bottom:0; width:3px; background:var(--border); }
```

## Status Badges

| Status | Class | Color |
|--------|-------|-------|
| Not started | `badge-todo` | Gray |
| In progress | `badge-progress` | Amber |
| Completed | `badge-done` | Green |

Status is read from `link-tracker.json` when generating. If all links in a portal are consumed, badge = completed.

## "What's New" Box (optional)

For regenerated portals, add a highlight box showing what changed:
```html
<div class="whats-new">
  <h3>🆕 What's New since [DATE]</h3>
  <ul>
    <li><strong>Feature</strong> - description</li>
  </ul>
</div>
```
CSS: `border: 2px solid #ff9800; border-radius: 12px; padding: 1.5rem;`

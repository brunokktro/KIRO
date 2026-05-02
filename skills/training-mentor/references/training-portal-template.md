# Training Portal HTML Template (Theory)

> APPROVED by Bruno on April 21, 2026. NEVER change the CSS or layout structure.
> Used for: crossplane-training.html, gitops-*-training.html

## CSS Variables (NEVER CHANGE)

```css
:root{
  --bg:#fff;
  --text:#1a1a2e;
  --card-bg:#f8f9fa;
  --border:#e0e0e0;
  --accent:#0073BB;
  --header-bg:#232F3E;
  --code-bg:#f4f4f4;
  --key-bg:#e8f4fd;
  --key-border:#b3d9f2;
  --shadow:rgba(0,0,0,.08);
  --v2-bg:#fff8e1;       /* Only for Crossplane v2 boxes */
  --v2-border:#ffb300;
  --v2-text:#5d4037;
}
[data-theme="dark"]{
  --bg:#1a1a2e;
  --text:#e0e0e0;
  --card-bg:#16213e;
  --border:#2a2a4a;
  --accent:#4fc3f7;
  --header-bg:#0f3460;
  --code-bg:#16213e;
  --key-bg:#1a2744;
  --key-border:#2a4a6a;
  --shadow:rgba(0,0,0,.3);
  --v2-bg:#2a2210;
  --v2-border:#ffb300;
  --v2-text:#ffe082;
}
```

## Badge Classes (NEVER CHANGE)

```css
.badge-important { background: #FFF3CD; color: #856404; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600; margin-right: 6px; }
.badge-notes { background: #D4EDDA; color: #155724; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600; margin-right: 6px; }
.badge-new { background: #d4edda; color: #155724; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600; margin-right: 6px; }
.badge-ai { background: #f8d7da; color: #721c24; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600; margin-right: 6px; }
```

## HTML Structure

```
<header>
  <button class="theme-toggle">
  <div class="container">
    <h1>EMOJI Title <span class="badge">VERSION</span></h1>
    <p>Subtitle description</p>
    <div class="meta">Generated DATE · Source info</div>
  </div>
</header>
<div class="container">
  <nav class="toc">
    <h2>📑 Table of Contents</h2>
    <div class="toc-group">GROUP NAME</div>  <!-- uppercase, for grouping modules -->
    <ol>
      <li><a href="#anchor">Module Name</a></li>
    </ol>
  </nav>

  <!-- One per module -->
  <section class="module" id="anchor">
    <h2>N. Module Title</h2>
    <p>Explanation paragraphs</p>
    <div class="key-concepts">
      <h4>🔑 Key Concepts</h4>
      <ul><li>...</li></ul>
    </div>
    <div class="v2-box">           <!-- Optional: only for Crossplane v2 changes -->
      <h4>What changes in v2.0</h4>
      <ul><li>...</li></ul>
    </div>
    <div class="hands-on">         <!-- Optional: inline quick commands -->
      <h4>🛠️ Try it yourself</h4>
      <pre><code>commands here</code></pre>
    </div>
    <div class="resources-grid">   <!-- 2-column: links left, videos right -->
      <div>
        <h4>📚 Docs & Reading</h4>
        <ul>
          <li><span class="badge-important">⭐ Important Reference</span><a href="...">Title</a></li>
          <li><span class="link-type">DOCS</span><a href="...">Title</a></li>
        </ul>
      </div>
      <div>
        <h4>🎬 Videos</h4>
        <!-- Video card with thumbnail -->
        <a class="vc" href="https://www.youtube.com/watch?v=ID" target="_blank">
          <div class="thumb"><img src="https://img.youtube.com/vi/ID/hqdefault.jpg" ...><span class="play">▶️</span></div>
          <div class="vtitle">Video Title</div>
        </a>
      </div>
    </div>
  </section>

  <!-- Labs link section (at the end, before footer) -->
  <section class="module" id="labs">
    <h2>🧪 Hands-On Labs</h2>
    <p>Labs detalhados no portal dedicado:</p>
    <p style="text-align:center;margin:24px 0">
      <a href="TOPIC-labs.html" style="display:inline-block;background:var(--accent);color:#fff;padding:12px 32px;border-radius:8px;text-decoration:none;font-weight:600;font-size:1.1rem">
        🧪 Abrir Labs Portal (N labs, L100-L400)
      </a>
    </p>
  </section>
</div>
<footer>...</footer>
<script>/* theme toggle + localStorage */</script>
```

## Key Layout Rules

- Max width: 960px centered
- Resources grid: `grid-template-columns: 1fr 1fr`, collapses to 1fr on mobile (700px)
- Video cards use YouTube thumbnail CDN (`img.youtube.com/vi/ID/hqdefault.jpg`), NEVER iframes
- Curated bookmarks (⭐ Important Reference) go ABOVE web-searched links
- OneNote notes (📝 Personal Notes) go alongside curated bookmarks
- Dark/light mode toggle persists via localStorage
- Each portal has unique localStorage key: `{topic}-theme`

## Variant: GitOps Style (gradient header)

GitOps portals use a gradient header instead of solid:
```css
header { background: linear-gradient(135deg, #232F3E 0%, #0073BB 100%); }
```
And fixed theme toggle button instead of inline:
```css
.theme-toggle { position: fixed; top: 1rem; right: 1rem; z-index: 100; border-radius: 50%; width: 44px; height: 44px; }
```
Both styles are approved. Use gradient for sub-trails, solid for standalone portals.

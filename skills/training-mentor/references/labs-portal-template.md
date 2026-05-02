# Labs Portal HTML Template

> APPROVED by Bruno on April 21, 2026. NEVER change the CSS or layout structure.
> Used for: crossplane-labs.html, gitops-labs.html

## CSS Variables (NEVER CHANGE)

```css
:root{
  --bg:#fff;
  --text:#1a1a2e;
  --card-bg:#f8f9fa;
  --border:#e0e0e0;
  --accent:#0073BB;
  --header-bg:#232F3E;
  --code-bg:#1e1e2e;       /* Dark code blocks - different from theory portals */
  --code-text:#cdd6f4;     /* Catppuccin-style light text on dark bg */
  --key-bg:#e8f4fd;
  --key-border:#b3d9f2;
  --shadow:rgba(0,0,0,.08);
  --success:#2e7d32;
  --warn-bg:#fff3cd;
  --warn-text:#856404;
  --ai-bg:#f8d7da;
  --ai-text:#721c24;
}
[data-theme="dark"]{
  --bg:#1a1a2e;
  --text:#e0e0e0;
  --card-bg:#16213e;
  --border:#2a2a4a;
  --accent:#4fc3f7;
  --header-bg:#0f3460;
  --code-bg:#11111b;
  --code-text:#cdd6f4;
  --key-bg:#1a2744;
  --key-border:#2a4a6a;
  --shadow:rgba(0,0,0,.3);
  --success:#66bb6a;
  --warn-bg:#3b2e00;
  --warn-text:#FEC448;
  --ai-bg:#2d1b1b;
  --ai-text:#f8d7da;
}
```

## Key Difference from Theory Portals
- Code blocks use DARK background (`#1e1e2e`) even in light mode - better readability for YAML/shell
- Labs use `.lab` class instead of `.module`
- Step numbers use circular badges (`.step-num`)
- Validation sections with green left border
- Prerequisites with amber left border

## Badge Classes (NEVER CHANGE)

```css
/* Difficulty level badges */
.badge-level { display:inline-block; padding:2px 10px; border-radius:12px; font-size:.75rem; font-weight:700; margin-right:8px; color:#fff; }
.l100 { background:#4caf50; }  /* Green */
.l200 { background:#ff9800; }  /* Orange */
.l300 { background:#f57c00; }  /* Dark orange */
.l400 { background:#d32f2f; }  /* Red */

/* Source badges */
.badge-ai { background:var(--ai-bg); color:var(--ai-text); padding:4px 10px; border-radius:6px; font-size:.78rem; font-weight:600; display:inline-block; margin-bottom:12px; }
.badge-real { background:#d4edda; color:#155724; padding:4px 10px; border-radius:6px; font-size:.78rem; font-weight:600; display:inline-block; margin-bottom:12px; }
```

## HTML Structure - Lab Section

```html
<section class="lab" id="labN">
  <!-- Badges: level + source -->
  <span class="badge-level lNNN">LNNN</span>
  <span class="badge-real">✅ Official Lab</span>
  <!-- OR -->
  <span class="badge-ai">⚠️ AI-Generated - Validate before use</span>

  <h2>Lab N: Title</h2>

  <!-- Objective box (blue left border) -->
  <div class="objective">
    <h4>🎯 Objective</h4>
    <p>What you'll accomplish in this lab.</p>
  </div>

  <!-- Prerequisites box (amber left border) -->
  <div class="prereqs">
    <h4>⚡ Prerequisites</h4>
    <ul>
      <li>Requirement 1</li>
      <li>Requirement 2</li>
    </ul>
  </div>

  <!-- Steps with numbered circles -->
  <h3><span class="step-num">1</span>Step Title</h3>
  <pre>kubectl apply -f manifest.yaml
# Comments explaining what happens
kubectl get resources -w</pre>

  <h3><span class="step-num">2</span>Next Step</h3>
  <pre>cat &lt;&lt;EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: example
data:
  key: value
EOF</pre>

  <!-- Validation box (green left border) -->
  <div class="validation">
    <h4>✅ Validation</h4>
    <ul>
      <li>Expected outcome 1</li>
      <li>Expected outcome 2</li>
    </ul>
  </div>

  <!-- Cleanup step (if applicable) -->
  <h3><span class="step-num">N</span>Cleanup</h3>
  <pre>kubectl delete -f manifest.yaml</pre>

  <!-- Reference links -->
  <div class="ref-links">
    <h4>📚 References</h4>
    <a href="..." target="_blank">Official docs link</a>
  </div>
</section>
```

## Key Layout Rules

- Each lab is a self-contained `<section class="lab">` card
- Steps use `<h3>` with `<span class="step-num">N</span>` circular badge
- Code blocks are `<pre>` with dark background - NO syntax highlighting library needed
- YAML manifests use `cat <<EOF | kubectl apply -f -` pattern for copy-paste friendliness
- Validation section ALWAYS present - tells user what to check
- Cleanup section for labs that create cloud resources (cost awareness)
- For official labs (external URL), provide brief description + link button, no inline steps
- For AI-generated labs, include full step-by-step inline with ⚠️ badge

## TOC Structure

```html
<nav class="toc">
  <h2>📋 Labs Index</h2>
  <ol>
    <li><span class="badge-level l100">L100</span><a href="#lab1">Lab Title</a></li>
    <li><span class="badge-level l200">L200</span><a href="#lab2">Lab Title</a></li>
    <!-- ... -->
  </ol>
</nav>
```

## When to Use Official vs AI-Generated

| Scenario | Approach |
|----------|----------|
| Official tutorial/workshop exists with step-by-step | `badge-real` + brief description + link to external source |
| Official docs have commands but no structured lab | `badge-real` + extract and structure the commands into lab format |
| No existing lab for the topic | `badge-ai` + create full step-by-step based on official docs |
| Paywall or broken link | NEVER include. Search for alternative or create AI-generated |

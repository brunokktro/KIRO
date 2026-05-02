# Dashboard HTML Template - Learning Curator

APPROVED PATTERN. Horizontal table layout with client-side pagination and filters.

## Layout Rules
- Horizontal table rows (NOT Kanban columns) to maximize items per page
- Client-side JS pagination: 15 items per page
- Filter buttons: All | Queued | In Progress | Consumed | Has Delivery
- Sort: delivery proximity first, then priority, then date added
- Compact rows: title (linked), type badge, topics as pills, delivery, time estimate, status
- Stats cards at top (same as before)
- Delivery-correlated items: orange left border
- No delivery: gray left border

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Learning Queue | [DATE]</title>
<style>
:root{--aws-orange:#FF9900;--aws-dark:#232F3E;--aws-light:#F2F3F3;--aws-blue:#147EBA;--green:#1B8A2E;--red:#D13212;--yellow:#F2A900;--gray:#687078;--border:#D5DBDB}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:var(--aws-light);color:#16191F;line-height:1.5;padding:16px}
.container{max-width:1200px;margin:0 auto}
.header{background:var(--aws-dark);color:white;padding:16px 24px;border-radius:10px 10px 0 0;display:flex;justify-content:space-between;align-items:center}
.header h1{font-size:20px;font-weight:600}
.header .meta{font-size:12px;opacity:.8;text-align:right}
.header .meta .date{color:var(--aws-orange);font-weight:600;font-size:14px}
.stats{display:grid;grid-template-columns:repeat(5,1fr);gap:8px;padding:12px 0}
.stat{background:white;border:1px solid var(--border);border-radius:6px;padding:10px;text-align:center}
.stat-value{font-size:22px;font-weight:700;color:var(--aws-dark)}
.stat-label{font-size:10px;color:var(--gray);text-transform:uppercase;letter-spacing:.5px}
.stat.highlight .stat-value{color:var(--aws-orange)}
.stat.success .stat-value{color:var(--green)}
.stat.warn .stat-value{color:var(--yellow)}
.filters{display:flex;gap:6px;padding:8px 0;flex-wrap:wrap}
.filter-btn{padding:4px 12px;border-radius:14px;border:1px solid var(--border);background:white;font-size:11px;cursor:pointer;font-weight:600;color:var(--gray)}
.filter-btn.active{background:var(--aws-dark);color:white;border-color:var(--aws-dark)}
.filter-btn:hover{border-color:var(--aws-orange)}
.table-wrap{background:white;border:1px solid var(--border);border-radius:0 0 10px 10px;overflow:hidden}
table{width:100%;border-collapse:collapse;font-size:12px}
th{background:var(--aws-dark);color:white;padding:8px 10px;text-align:left;font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:.3px;white-space:nowrap}
td{padding:8px 10px;border-bottom:1px solid var(--border);vertical-align:top}
tr:hover td{background:#F7F8F8}
tr.has-delivery td:first-child{border-left:3px solid var(--aws-orange)}
tr.no-delivery td:first-child{border-left:3px solid var(--border)}
.item-title a{color:var(--aws-dark);text-decoration:none;font-weight:600}
.item-title a:hover{color:var(--aws-blue);text-decoration:underline}
.topic-tag{display:inline-block;padding:1px 5px;border-radius:3px;font-size:9px;font-weight:600;margin-right:3px;background:#E3F2FD;color:var(--aws-blue)}
.type-badge{display:inline-block;padding:1px 6px;border-radius:3px;font-size:9px;font-weight:600;background:#FFF8E1;color:#B8860B}
.status-badge{display:inline-block;padding:1px 6px;border-radius:3px;font-size:9px;font-weight:600}
.status-queued{background:var(--aws-light);color:var(--gray)}
.status-in-progress{background:#E3F2FD;color:var(--aws-blue)}
.status-consumed{background:#E6F4EA;color:var(--green)}
.delivery-text{font-size:11px;color:var(--aws-orange);font-weight:600}
.priority-high{color:var(--red);font-weight:700}
.priority-medium{color:var(--yellow);font-weight:600}
.priority-low{color:var(--gray)}
.pagination{display:flex;justify-content:center;align-items:center;gap:8px;padding:12px}
.page-btn{padding:4px 10px;border:1px solid var(--border);border-radius:4px;background:white;cursor:pointer;font-size:11px}
.page-btn.active{background:var(--aws-dark);color:white}
.page-btn:hover{border-color:var(--aws-orange)}
.page-info{font-size:11px;color:var(--gray)}
.footer{text-align:center;padding:12px;font-size:11px;color:var(--gray)}
.empty{text-align:center;padding:24px;color:var(--gray);font-size:13px}
</style>
</head>
<body>
<div class="container">

<div class="header">
  <div>
    <h1>Learning Queue</h1>
    <div style="font-size:12px;opacity:.7;margin-top:2px">Personal Learning Backlog</div>
  </div>
  <div class="meta">
    <div class="date">[DATE]</div>
    <div>[TOTAL] items | [DELIVERY_COUNT] linked to deliveries</div>
  </div>
</div>

<div class="stats">
  <div class="stat highlight"><div class="stat-value">[N]</div><div class="stat-label">Queued</div></div>
  <div class="stat"><div class="stat-value">[N]</div><div class="stat-label">In Progress</div></div>
  <div class="stat success"><div class="stat-value">[N]</div><div class="stat-label">Consumed (month)</div></div>
  <div class="stat warn"><div class="stat-value">[N]</div><div class="stat-label">With Delivery</div></div>
  <div class="stat"><div class="stat-value">[N]h</div><div class="stat-label">Total Est. Time</div></div>
</div>

<div class="filters">
  <button class="filter-btn active" onclick="filterItems('all')">All</button>
  <button class="filter-btn" onclick="filterItems('queued')">Queued</button>
  <button class="filter-btn" onclick="filterItems('in-progress')">In Progress</button>
  <button class="filter-btn" onclick="filterItems('consumed')">Consumed</button>
  <button class="filter-btn" onclick="filterItems('delivery')">Has Delivery</button>
</div>

<div class="table-wrap">
<table>
<thead>
<tr>
  <th>Title</th>
  <th>Type</th>
  <th>Topics</th>
  <th>Priority</th>
  <th>Est.</th>
  <th>Feeds Delivery</th>
  <th>Status</th>
  <th>Added</th>
</tr>
</thead>
<tbody id="items">
<!-- JS populates rows from DATA array -->
</tbody>
</table>
<div class="empty" id="empty-msg" style="display:none">Nenhum item encontrado</div>
</div>

<div class="pagination" id="pagination"></div>

<div class="footer">Gerado por R2D2 | learning-curator skill | [TIMESTAMP]</div>

</div>

<script>
const DATA = [/*ITEMS_DATA*/];
const PER_PAGE = 15;
let currentFilter = 'all';
let currentPage = 1;

function filterItems(f) {
  currentFilter = f;
  currentPage = 1;
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  event.target.classList.add('active');
  render();
}

function getFiltered() {
  if (currentFilter === 'all') return DATA;
  if (currentFilter === 'delivery') return DATA.filter(i => i.feedsDelivery);
  return DATA.filter(i => i.status === currentFilter);
}

function render() {
  const filtered = getFiltered();
  const totalPages = Math.ceil(filtered.length / PER_PAGE);
  const start = (currentPage - 1) * PER_PAGE;
  const page = filtered.slice(start, start + PER_PAGE);
  const tbody = document.getElementById('items');
  const empty = document.getElementById('empty-msg');

  if (!page.length) { tbody.innerHTML = ''; empty.style.display = 'block'; }
  else {
    empty.style.display = 'none';
    tbody.innerHTML = page.map(i => {
      const cls = i.feedsDelivery ? 'has-delivery' : 'no-delivery';
      const topics = i.topics.map(t => `<span class="topic-tag">${t}</span>`).join('');
      const statusCls = `status-${i.status}`;
      const priCls = `priority-${i.priority}`;
      const delivery = i.feedsDelivery ? `<span class="delivery-text">${i.feedsDelivery}</span>` : '<span style="color:var(--gray)">-</span>';
      return `<tr class="${cls}">
        <td class="item-title"><a href="${i.url}" target="_blank">${i.title}</a></td>
        <td><span class="type-badge">${i.type}</span></td>
        <td>${topics}</td>
        <td><span class="${priCls}">${i.priority}</span></td>
        <td>${i.estimatedMinutes}m</td>
        <td>${delivery}</td>
        <td><span class="status-badge ${statusCls}">${i.status}</span></td>
        <td style="white-space:nowrap">${i.addedAt}</td>
      </tr>`;
    }).join('');
  }

  // Pagination
  const pag = document.getElementById('pagination');
  if (totalPages <= 1) { pag.innerHTML = ''; return; }
  let html = `<span class="page-info">${filtered.length} items</span>`;
  for (let p = 1; p <= totalPages; p++) {
    html += `<button class="page-btn ${p===currentPage?'active':''}" onclick="goPage(${p})">${p}</button>`;
  }
  pag.innerHTML = html;
}

function goPage(p) { currentPage = p; render(); }

render();
</script>
</body>
</html>
```

## Rendering Rules
- DATA array: inject the queue.json items directly as JS array
- Sort before injecting: delivery items first (by proximity), then priority, then addedAt
- has-delivery class: orange left border on first td
- no-delivery class: gray left border
- Pagination: 15 items per page, buttons at bottom
- Filters: client-side JS, no server needed
- Stats: calculate from DATA array counts
- Total Est. Time: sum of estimatedMinutes / 60, rounded to 1 decimal

## Chart.js Enhancement (Queue Visual Summary)

Add Chart.js CDN once in `<head>`:
```html
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
```

Place a two-column chart section between stat cards and filter buttons:
- **Left: Donut** - Queue Status (Queued=gray, In Progress=blue, Consumed=green). Shows progress at a glance.
- **Right: Bar (horizontal)** - Top Topics by item count. `indexAxis: 'y'`, single color (--aws-blue), `borderRadius: 6`.
- Both wrapped in `.chart-wrap` divs inside a 2-column grid
- Filter buttons, paginated table, and all interactive JS remain UNCHANGED below the charts

Add to CSS:
```css
.charts-row{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px}
.chart-wrap{background:white;border:1px solid var(--border);border-radius:8px;padding:12px}
.chart-wrap h4{font-size:12px;color:var(--aws-blue);margin-bottom:8px}
canvas{max-height:180px}
```

Chart.js v4 rules: `indexAxis: 'y'` for horizontal bars (NEVER `'horizontal'`), omit indexAxis for vertical, always `borderRadius: 6`.

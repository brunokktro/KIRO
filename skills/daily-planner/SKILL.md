---
name: daily-planner
description: >
  Daily and weekly planning assistant that integrates your calendar and task manager
  to produce Eisenhower-prioritized briefings, identify deep work opportunities, and
  manage task triage. Enforces time boxing rules, conflict detection, and capacity limits.
  Activate on: "daily briefing", "plan my day", "weekly planning", "plan my week",
  "task triage", "add task", "block time", "time box", "reorganize schedule",
  "what's on my plate", "how does my day look".
metadata:
  version: "1.0.0"
---

# Daily Planner

Planning assistant that integrates your calendar and task manager to organize your day,
week, and task backlog aligned with your strategic priorities.

Adapt the MCP tools section to your stack. This skill is designed around:
- **Calendar:** any MCP-connected calendar (Outlook, Google Calendar, etc.)
- **Tasks:** any MCP-connected task manager (TickTick, Todoist, Linear, etc.)

---

## Core Principles

### Eisenhower Matrix
Classify every task before scheduling:

| | Urgent | Not Urgent |
|---|---|---|
| **Important** | Q1 - Do Now | Q2 - Schedule |
| **Not Important** | Q3 - Delegate/Quick | Q4 - Eliminate |

- Q1: deadline imminent + direct impact on customers/deliverables
- Q2: important but no hard deadline - schedule a time box
- Q3: urgent but low impact - batch or delegate
- Q4: neither - eliminate or defer indefinitely
- **Do not inflate Q1.** If everything is Q1, nothing is a priority.

### Time Boxing Rules (ABSOLUTE)
- Time boxes are ALWAYS in the morning (e.g., 8AM-12PM). Afternoons stay free for calls and meetings.
- Max 1 time box per morning. Never stack multiple deep work blocks on the same day.
- Writing tasks (blog posts, documents, reports) = 3h blocks, not 2h.
- Never schedule prep on the same day as a delivery - prep must be at least 1 day before.
- When a day has a customer/external delivery in the afternoon, the morning MUST be final prep for that delivery (or left empty). Never schedule an unrelated time box on a delivery day.
- Never place time boxes on weekends, holidays, or travel days.

### Daily Task Load Limits
- Max 4 tasks per normal work day
- Max 2 tasks on delivery days (workshop, talk, external call > 1h)
- If redistribution exceeds the limit for any day, cascade overflow to the next available day
- Always show a load summary before confirming redistribution

### Calendar Protection
- Only move/create/update events you own and that are explicitly time boxes
- Never delete calendar events - always update (move) to preserve content and links
- Events with other attendees: hands-off
- Recurring series: hands-off (user manages manually)
- When in doubt, ask. Calendar is sacred.

---

## Configuration (adapt to your stack)

Before using this skill, replace the placeholders below with your actual tool names and IDs:

```
CALENDAR_TOOL: <your calendar MCP tool>        # e.g., outlook-calendar_view, gcal_list_events
TASK_TOOL: <your task manager MCP tool>        # e.g., ticktick_list_tasks, todoist_get_tasks
TASK_CREATE: <your task creation tool>         # e.g., ticktick_create_task, todoist_add_task
TASK_UPDATE: <your task update tool>           # e.g., ticktick_update_task, todoist_update_task
PROJECT_ID: <your main project/inbox ID>       # e.g., inbox123456, project_abc
TIMEZONE: <your timezone>                      # e.g., America/Sao_Paulo, America/New_York
```

---

## Job 1: Daily Briefing

**Triggers:** "daily briefing", "plan my day", "how does my day look", "what's on my plate"

**Steps:**

1. Fetch today's calendar events
2. Convert all times to local timezone
3. Fetch today's tasks (due today)
4. Fetch overdue tasks (past due, not completed)
5. Classify all tasks in Eisenhower quadrants
6. Identify free gaps in the calendar
7. Match Q1/Q2 tasks to available gaps

**Output format:**

```
## Today's Timeline (DD/MMM)

| Time | Event | Type |
|------|-------|------|
| 08:00-12:00 | [Time Box] Deep Work: XYZ | Deep work |
| 12:00-13:00 | FREE | Gap |
| 14:00-15:00 | Customer Call - Acme Corp | Meeting |

## Available Gaps
- 12:00-13:00 (1h) - suggestion: [most urgent Q1 task]
- 16:00-17:00 (1h) - suggestion: [Q2 task]

## Tasks (Eisenhower)

**Q1 - Do Now:**
- [ ] Task X (due: DD/MMM)

**Q2 - Schedule:**
- [ ] Task Y

**Q3 - Delegate/Quick:**
- [ ] Task Z

**Overdue:**
- [ ] Task W (was due DD/MMM)

## Suggested Actions
1. Use the 12:00-13:00 gap for [task]
2. [Other suggestions based on priorities]
```

---

## Job 2: Weekly Planning

**Triggers:** "weekly planning", "plan my week", "organize my week", "weekly briefing"

**Steps:**

1. Fetch calendar events for the next 2 weeks (Mon-Fri only)
2. Convert all times to local timezone
3. Fetch tasks due in the next 14 days
4. Fetch ALL undone tasks including those without due dates (backlog)
5. Identify deliveries (workshops, talks, demos) - these are immovable anchors
6. Cross-reference undated tasks with upcoming deliveries by topic/technology/customer
7. Propose due dates for undated tasks that correlate with upcoming deliveries
8. Validate capacity per day (max 4 tasks, max 1 morning time box)

**Undated task intelligence:**
When running weekly planning, always fetch tasks WITHOUT due dates and cross-reference with upcoming calendar deliveries. Assign due dates to tasks that correlate by topic, technology, or customer name. Tasks without correlation stay in backlog.

```
Undated tasks that correlate with upcoming deliveries:
- "Study ArgoCD GitOps" → Apr 27 (day before ArgoCD workshop prep)
- "Review K8s networking" → May 5 (feeds EKS Networking talk)
-> Approve date assignment?
```

**Output format:**

```
## Week 1: DD/MMM - DD/MMM

| Day | Meetings | Deep Work Gaps | Tasks Due |
|-----|----------|----------------|-----------|
| Mon | 3 | 4h (08-12) | 2 |
| Tue | 5 | 0h | 1 |
| Wed | 2 | 4h (08-12) | 0 |
| Thu | 4 | 0h | 3 |
| Fri | 1 | 4h (08-12) | 1 |

### Busiest Day: [day] - [X meetings, 0 gaps]
### Best Day for Deep Work: [day] - [Xh free]

## Week 2: DD/MMM - DD/MMM
[same format]

## Tasks (Eisenhower)
[same format as Job 1]

## Time Boxing Suggestions
1. [Day] morning: work on [Q1 task] (feeds delivery on DD/MMM)
2. [Day] morning: [Q2 task]

## Conflicts & Risks
- [list of scheduling conflicts]

## Undated Tasks → Proposed Dates
| Task | Proposed Date | Reason |
|------|--------------|--------|
| Study ArgoCD | Apr 27 | Feeds workshop Apr 28 |
```

---

## Job 3: Task Triage

**Triggers:** "add task", "new task", "task triage", "create task", "I need to do"

**Steps:**

1. User describes task(s) in free text
2. Extract: short clean title, context/links for description
3. Classify in Eisenhower using current priorities as reference
4. Propose the formatted task before creating:
   - Title
   - Priority (Q1/Q2/Q3/Q4)
   - Description (links, context, sub-items)
   - Due date (if applicable)
5. Wait for confirmation
6. Create via task manager tool

**Formatting rules:**
- Title: verb + object, max ~60 chars. Example: "Prepare demo for Acme Corp workshop"
- Description: full links, context in text, sub-items as a), b), c)
- If user sends multiple items at once, propose all in a table before creating

**Prioritization rules:**
- Do not inflate Q1: Q1 = imminent deadline + direct customer/pipeline impact
- Study tasks without a fixed date: no due date. Use calendar time boxes to schedule them.
- Sub-tasks of the same engagement go as a), b), c) in the description of one task
- Always propose the full table and wait for confirmation before creating
- Q1 tasks with implicit deadlines should have explicit due dates - suggest when user doesn't define

**Proposal format:**

```
| # | Title | Priority | Due | Description |
|---|-------|----------|-----|-------------|
| 1 | Prepare demo for Acme Corp | Q1 | Apr 28 | Workshop prep\na) slides\nb) demo env |
| 2 | Read K8s networking book | Q2 | - | No deadline, schedule via time box |

Confirm to create?
```

---

## Job 4: Time Box Scheduling

**Triggers:** "block time", "time box", "schedule deep work", "add time boxing", "reserve slot"

**Steps:**

1. User describes what to block/schedule
2. Check availability for the target date
3. Propose the event with full details:
   - Subject: `[Time Box] <type>: <description>`
   - Date, start/end time (morning only, 8AM-12PM)
   - Reminder: 15 minutes before (default)
4. Run pre-execution conflict check:
   - Fetch target day's full calendar
   - Build timeline with all events
   - Check for overlaps with existing events
   - Verify no afternoon placement, no delivery day conflict
5. Show the simulation and wait for explicit confirmation
6. Only after "ok" / "approve" / "go ahead" - create the event

**Pre-execution simulation format:**

```
Day DD/MMM - Simulation:
08:00-12:00 [Time Box] Prep: XYZ (NEW)
12:00-13:00 Lunch (existing)
14:00-15:00 Customer Call (existing)
-> No conflicts. Execute?
```

**If conflict detected:**
- Show the conflict clearly
- Propose an alternative date/time
- Never execute a conflicting write

---

## Job 5: Schedule Reorganization

**Triggers:** "reorganize schedule", "reorganize my week", "reprioritize", "adjust calendar"

**This is the most complex job. Follow this exact sequence:**

### Phase 1: Data Collection (run in parallel)
1. Fetch calendar for the target period (split into 7-day chunks)
2. Fetch ALL undone tasks including undated ones
3. Fetch overdue tasks

### Phase 2: Analysis (before ANY writes)
1. Build day-by-day timeline
2. Identify immovable anchors (deliveries, external commitments)
3. Flag time box violations:
   - Afternoon time boxes
   - Multiple time boxes on same morning
   - Prep on same day as delivery
   - Unrelated time box on delivery day morning
   - Time boxes on holidays/weekends/travel days
4. Cross-reference ALL tasks (with AND without dates) against deliveries
5. Validate capacity: max 1 morning time box + max 4 tasks per day
6. Check Eisenhower quadrants: are Q1 tasks actually urgent+important?

### Phase 3: Proposal (MANDATORY before execution)
Present the complete reorganization plan:

```
## Rational Distribution (DD/MMM - DD/MMM)

Day DD (Mon) - [Morning Time Box]:
- [Task 1] (feeds delivery on DD/MMM)
- [Task 2] (same topic as time box)
- [Quick admin task] (30min, between calls)

Day DD (Tue) - [Morning Time Box]:
- ...

## Deferred to next period:
- [Item moved] (reason: lower priority than X)
```

### Phase 4: Execution (only after approval)
1. Calendar updates: always UPDATE (never delete) to preserve event content
2. Task updates: use individual update calls (not batch) for due date changes
3. Verify: spot-check 2-3 items after update to confirm changes applied

---

## Conflict Detection (run before every calendar write)

Before executing ANY calendar write:

1. Fetch the target day's full calendar
2. Build a timeline of all events with start/end times
3. Check for conflicts:
   - No overlap with any existing event
   - Time box only in morning slot (8AM-12PM)
   - No time box on delivery days (unless it's prep for that delivery)
   - No time box on travel/holiday days
4. Present the simulation to the user
5. Only execute after confirmation

---

## Displacement Priority Logic

When moving items to a week that already has time boxes:

1. Never treat existing time boxes as immovable - all time boxes are movable
2. Compare priorities: which time box has a closer delivery dependency?
3. Time boxes feeding a delivery in the next 2 weeks win over generic study/dive deeps
4. If an existing time box has no delivery correlation, it can be displaced
5. Always present the trade-off: "Moving [existing] to [new date] to make room for [higher priority] because [delivery X on date Y]"
6. The goal is not to find empty slots - it's to ensure the RIGHT items are in the RIGHT slots based on delivery proximity

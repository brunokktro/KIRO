---
name: "power-ticktick"
displayName: "TickTick"
description: "Personal task management via TickTick MCP. Query, create, and manage tasks with Eisenhower Matrix prioritization."
keywords: ["ticktick", "tasks", "todo", "personal tasks", "task management", "eisenhower", "matrix", "priorities", "reminders", "daily planning", "weekly planning"]
---

# TickTick MCP Power

Personal task management via TickTick MCP. Query, create, and manage tasks and lists directly from Kiro.

## Authentication

Uses OAuth via Streamable HTTP. On first connection, follow the browser prompt to sign in and authorize.
No additional auth tools needed - uses TickTick OAuth directly.

## Eisenhower Matrix

This Power is designed to work with the Eisenhower Matrix as the primary task view.
Priority values map to quadrants:

| Priority | Quadrant | Meaning |
|----------|----------|---------|
| 5 | Q1 | Urgent + Important (Do First) |
| 3 | Q2 | Important + Not Urgent (Schedule) |
| 1 | Q3 | Urgent + Not Important (Delegate) |
| 0 | Q4 | Not Urgent + Not Important (Eliminate/Backlog) |

## Configuration

After installing, find your project IDs:
- Use `list_projects` to get all project IDs
- Set your main inbox/default project ID in your steering file
- Recommended: use a single inbox project with Eisenhower Matrix view rather than multiple projects

## Key Learnings (Gotchas)

### Task content (notes inside a task)
- Use the `content` field, NOT `notes`. The `notes` field in `create_task` does NOT persist.
- Always include `content` in the `create_task` call when creating tasks with notes.
- `update_task` with `content` field works for updating existing task notes.
- Sub-items go in `content` as a), b), c) - NOT as separate tasks.
- Keep task title clean and short. Put links, details, and sub-items in `content`.

### Batch operations
- `batch_update_tasks` works reliably for `priority` changes only.
- For `dueDate` changes, always use individual `update_task` calls - batch silently fails for dates.
- For `content` updates, prefer individual `update_task` calls.

### Due dates and reminders
- When setting a due date, use a morning time (e.g., `T07:00:00.000-0300` for 7 AM BRT).
- Avoid end-of-day times (`T23:59`) - notifications arrive too late.
- Always include a `reminders` entry when setting due dates so the user gets a push notification.
- Reminder trigger format: `"TRIGGER:PT0S"` (fires at due time).
- Tasks without dates are valid - not every task needs a deadline.

### Task structure
- The `columnId` field relates to Kanban columns within a project (not needed for simple inbox use).
- No delete tool available in MCP - task deletion must be done manually in the app.

## Available Tools

### Task Queries
- `list_undone_tasks_by_time_query` - today, tomorrow, next7day, last7day
- `list_undone_tasks_by_date` - custom date range (max 14 days)
- `search_task` / `search` - keyword search
- `get_task_by_id` - full task details including content
- `filter_tasks` - filter by priority, project, tag, status

### List/Project Queries
- `list_projects` - all projects and their IDs
- `get_project_with_undone_tasks` - project + all undone tasks (includes undated tasks)

### Task Management
- `create_task` - create with content included in the same call
- `update_task` - update priority, title, dates, and content
- `complete_task` - mark done
- `move_task` - move between projects
- `batch_add_tasks` - create multiple tasks at once
- `batch_update_tasks` - update multiple (reliable for priority; use individual calls for dates/content)

## Keywords

ticktick, tasks, todo, personal tasks, task management, eisenhower, matrix, priorities, reminders, lists, daily planning, weekly planning

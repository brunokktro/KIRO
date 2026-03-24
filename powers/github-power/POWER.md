---
name: "github-power"
displayName: "GitHub Power"
description: "Complete GitHub integration for repository management, issues, pull requests, file operations, and code search. Manage your GitHub workflow directly from Kiro."
keywords: ["github", "git", "repository", "pull-request", "issue", "code-review"]
author: "Kiro Team"
---

# GitHub Power

## Overview

GitHub Power provides comprehensive GitHub integration, enabling you to manage repositories, issues, pull requests, and files without leaving your development environment. Whether you're reviewing code, managing issues, or searching across repositories, this power streamlines your GitHub workflow.

Key capabilities:
- Repository management (create, fork, search)
- File operations (read, create, update, push multiple files)
- Issue tracking (create, update, list, comment)
- Pull request workflow (create, review, merge, update)
- Branch management (create, list commits)
- Code and repository search
- User search

Perfect for developers who want to integrate GitHub operations into their coding workflow.

## Onboarding

### Prerequisites
- GitHub account
- GitHub Personal Access Token (PAT) with appropriate permissions

### Installation

1. Generate a GitHub Personal Access Token:
   - Go to https://github.com/settings/tokens
   - Click "Generate new token (classic)"
   - Select scopes: `repo`, `read:org`, `user`, `workflow`
   - Copy the generated token

2. The GitHub MCP server will be configured via this power's mcp.json

### Configuration

Set your GitHub PAT as an environment variable in the mcp.json configuration (see MCP Config Placeholders section below).

## Common Workflows

### Workflow 1: Search and Explore Repositories

**Goal:** Find repositories by topic, language, or keywords

**Example:**
```
Use tool: search_repositories
Parameters:
  query: "language:python stars:>1000 machine-learning"
  perPage: 10
```

**Search Syntax Tips:**
- `language:python` - Filter by language
- `stars:>1000` - Repositories with 1000+ stars
- `user:username` - Repositories by specific user
- `org:organization` - Repositories in organization
- `topic:machine-learning` - By topic

---

### Workflow 2: Read Repository Files

**Goal:** Read file contents from any repository

**Example:**
```
Use tool: get_file_contents
Parameters:
  owner: "microsoft"
  repo: "vscode"
  path: "README.md"
  branch: "main"
```

---

### Workflow 3: Create or Update Files

**Goal:** Create new files or update existing ones in a repository

**Example:**
```
Use tool: create_or_update_file
Parameters:
  owner: "yourusername"
  repo: "your-repo"
  path: "src/newfile.js"
  content: "console.log('Hello World');"
  message: "Add new feature"
  branch: "main"
```

**Note:** For updating existing files, you need the file's SHA (get it via get_file_contents first)

---

### Workflow 4: Push Multiple Files at Once

**Goal:** Commit multiple files in a single operation

**Example:**
```
Use tool: push_files
Parameters:
  owner: "yourusername"
  repo: "your-repo"
  branch: "main"
  message: "Update multiple files"
  files: [
    {
      "path": "src/file1.js",
      "content": "// File 1 content"
    },
    {
      "path": "src/file2.js",
      "content": "// File 2 content"
    }
  ]
```

---

### Workflow 5: Create and Manage Issues

**Goal:** Track bugs, features, and tasks

**Create Issue:**
```
Use tool: create_issue
Parameters:
  owner: "yourusername"
  repo: "your-repo"
  title: "Bug: Login fails on mobile"
  body: "Description of the issue..."
  labels: ["bug", "mobile"]
```

**List Issues:**
```
Use tool: list_issues
Parameters:
  owner: "yourusername"
  repo: "your-repo"
  state: "open"
  labels: ["bug"]
```

**Update Issue:**
```
Use tool: update_issue
Parameters:
  owner: "yourusername"
  repo: "your-repo"
  issue_number: 42
  state: "closed"
```

---

### Workflow 6: Pull Request Workflow

**Create PR:**
```
Use tool: create_pull_request
Parameters:
  owner: "yourusername"
  repo: "your-repo"
  title: "Add new feature"
  head: "feature-branch"
  base: "main"
  body: "Description of changes..."
```

**Review PR:**
```
Use tool: create_pull_request_review
Parameters:
  owner: "yourusername"
  repo: "your-repo"
  pull_number: 123
  body: "Looks good overall, minor suggestions"
  event: "APPROVE"
  comments: [
    {
      "path": "src/file.js",
      "line": 42,
      "body": "Consider using const here"
    }
  ]
```

**Merge PR:**
```
Use tool: merge_pull_request
Parameters:
  owner: "yourusername"
  repo: "your-repo"
  pull_number: 123
  merge_method: "squash"
```

---

### Workflow 7: Branch Management

**Create Branch:**
```
Use tool: create_branch
Parameters:
  owner: "yourusername"
  repo: "your-repo"
  branch: "feature-new-ui"
  from_branch: "main"
```

**List Commits:**
```
Use tool: list_commits
Parameters:
  owner: "yourusername"
  repo: "your-repo"
  sha: "main"
  perPage: 10
```

---

### Workflow 8: Search Code

**Goal:** Find code across GitHub repositories

**Example:**
```
Use tool: search_code
Parameters:
  q: "function authenticate repo:yourusername/your-repo"
  per_page: 10
```

**Search Tips:**
- `repo:owner/name` - Search in specific repo
- `language:javascript` - Filter by language
- `path:src/` - Search in specific path
- `extension:js` - Filter by file extension

---

### Workflow 9: Fork Repository

**Goal:** Create a fork for contributing

**Example:**
```
Use tool: fork_repository
Parameters:
  owner: "original-owner"
  repo: "original-repo"
  organization: "your-org"
```

---

### Workflow 10: Create Repository

**Goal:** Create a new repository

**Example:**
```
Use tool: create_repository
Parameters:
  name: "my-new-project"
  description: "A cool new project"
  private: false
  autoInit: true
```

## Troubleshooting

### Authentication Errors

**Problem:** "Bad credentials" or "401 Unauthorized"
**Cause:** Invalid or expired GitHub token
**Solution:**
1. Verify your PAT is correct in mcp.json
2. Check token hasn't expired
3. Ensure token has required scopes (repo, read:org, user)
4. Generate new token if needed

---

### Permission Denied

**Problem:** "403 Forbidden" or "Resource not accessible"
**Cause:** Insufficient permissions
**Solution:**
1. Verify you have write access to the repository
2. Check if repository is private and token has access
3. For organization repos, ensure token has org permissions

---

### File Not Found

**Problem:** "404 Not Found" when reading files
**Cause:** Incorrect path, branch, or repository
**Solution:**
1. Verify repository owner and name are correct
2. Check file path is accurate (case-sensitive)
3. Ensure branch name is correct (default may be 'main' or 'master')
4. Confirm file exists in the specified branch

---

### SHA Required for Update

**Problem:** "SHA required" when updating files
**Cause:** Updating existing file without providing SHA
**Solution:**
1. First use get_file_contents to get current file
2. Extract the SHA from the response
3. Include SHA in create_or_update_file call

---

### Rate Limiting

**Problem:** "API rate limit exceeded"
**Cause:** Too many requests in short time
**Solution:**
1. Wait for rate limit to reset (check response headers)
2. Use authenticated requests (higher limits)
3. Reduce frequency of requests
4. Consider caching results

## Best Practices

- Always use descriptive commit messages
- Create feature branches instead of committing directly to main
- Review PR files and status before merging
- Use labels to organize issues effectively
- Search before creating duplicate issues
- Use draft PRs for work-in-progress
- Add reviewers to PRs for code review
- Close issues when resolved with reference to PR
- Use push_files for multiple file changes (more efficient)
- Keep PAT secure and rotate regularly

## Configuration

**Environment Variables:**
- `GITHUB_PERSONAL_ACCESS_TOKEN`: Your GitHub PAT (required)

## MCP Config Placeholders

**IMPORTANT:** Before using this power, replace the following placeholder in `mcp.json`:

- **`YOUR_GITHUB_PAT_HERE`**: Your GitHub Personal Access Token
  - **How to get it:**
    1. Go to https://github.com/settings/tokens
    2. Click "Generate new token (classic)"
    3. Select scopes: `repo`, `read:org`, `user`, `workflow`
    4. Copy the generated token
    5. Store it securely (you won't be able to see it again)

**After replacing the placeholder, your mcp.json should look like:**
```json
{
  "mcpServers": {
    "github": {
      "type": "stdio",
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-github"
      ],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_your_actual_token_here"
      }
    }
  }
}
```

---

**Package:** `@modelcontextprotocol/server-github`
**MCP Server:** github

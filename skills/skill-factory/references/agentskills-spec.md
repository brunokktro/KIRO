# Agent Skills Specification Reference

Source: https://agentskills.io/specification

## Directory structure
A skill is a directory containing at minimum a `SKILL.md` file.

### Optional directories

#### scripts/
Contains executable code that agents can run. Scripts should:
- Be self-contained or clearly document dependencies
- Include helpful error messages
- Handle edge cases gracefully

#### references/
Contains additional documentation agents can read when needed:
- `REFERENCE.md` — Detailed technical reference
- Domain-specific files (e.g., `finance.md`, `legal.md`)
- Keep individual files focused — agents load these on demand

#### assets/
Contains static resources:
- Templates (document templates, configuration templates)
- Images (diagrams, examples)
- Data files (lookup tables, schemas)

## Frontmatter fields

### name (required)
- 1-64 characters
- Lowercase alphanumeric and hyphens only
- Cannot start/end with hyphen
- No consecutive hyphens
- Must match parent directory name

### description (required)
- 1-1024 characters
- Should describe what the skill does AND when to use it
- Include specific keywords that help agents identify relevant tasks

### license (optional)
Short license name or reference to bundled license file.

### compatibility (optional)
- 1-500 characters
- Environment requirements (product, system packages, network access)

### metadata (optional)
Arbitrary key-value mapping for additional metadata (author, version, etc.).

### allowed-tools (optional, experimental)
Space-delimited list of pre-approved tools the skill may use.

## File references
Use relative paths from the skill root:
```
See [the reference guide](references/REFERENCE.md) for details.
Run the extraction script: scripts/extract.py
```

Keep file references one level deep from `SKILL.md`. Avoid deeply nested reference chains.

## Validation
Use the skills-ref library to validate:
```
skills-ref validate ./my-skill
```

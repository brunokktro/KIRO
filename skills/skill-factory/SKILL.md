---
name: skill-factory
description: Guide the creation of new Kiro skills following the Agent Skills specification. Use this skill when the user wants to create, scaffold, or validate a new skill from scratch, ensuring correct directory structure, frontmatter, progressive disclosure, and references.
---

# Skill Factory

## When to use this skill
Use this skill when the user needs to:
- Create a new skill from scratch
- Scaffold the directory structure for a skill
- Validate an existing skill against the Agent Skills spec
- Understand how to structure skill content for progressive disclosure

## Skill directory structure
Every skill is a directory containing at minimum a `SKILL.md` file:

```
skill-name/
├── SKILL.md              # Required — main instructions
├── references/            # Optional — detailed docs loaded on demand
│   └── REFERENCE.md
├── scripts/               # Optional — executable code agents can run
│   └── script.py
└── assets/                # Optional — templates, images, data files
    └── template.md
```

## Default installation path
Skills should be created at: `~/.kiro/skills/` (user-level, available across all workspaces).

## SKILL.md format

### Frontmatter (required)
```yaml
---
name: skill-name
description: What this skill does and when to use it.
---
```

| Field | Required | Rules |
|-------|----------|-------|
| `name` | Yes | Max 64 chars. Lowercase, numbers, hyphens only. Must match directory name. |
| `description` | Yes | Max 1024 chars. Describe what it does AND when to use it. Include keywords for activation. |
| `license` | No | License name or reference to bundled file. |
| `compatibility` | No | Max 500 chars. Environment requirements. |
| `metadata` | No | Arbitrary key-value pairs (author, version, etc.). |
| `allowed-tools` | No | Space-delimited list of pre-approved tools. Experimental. |

### Name rules
- Only lowercase alphanumeric and hyphens (`a-z`, `0-9`, `-`)
- Cannot start or end with `-`
- No consecutive hyphens (`--`)

### Body content
The markdown body after frontmatter contains skill instructions. Recommended sections:
- Step-by-step instructions
- Examples of inputs and outputs
- Common edge cases
- Reference to files in `references/` for detailed content

## Progressive disclosure
Structure skills for efficient context usage:
1. **Metadata** (~100 tokens): `name` and `description` loaded at startup for all skills
2. **Instructions** (< 5000 tokens): Full `SKILL.md` body loaded when skill is activated
3. **Resources** (as needed): Files in `references/`, `scripts/`, `assets/` loaded only when required

Keep `SKILL.md` under 500 lines. Move detailed reference material to separate files.

## Creation workflow
1. Ask the user what the skill should do and when it should activate
2. Choose a name (lowercase, hyphens, max 64 chars)
3. Write a clear `description` with activation keywords
4. Create `SKILL.md` with frontmatter and instructions
5. If the skill needs detailed reference docs, create `references/` files
6. If the skill needs scripts, create `scripts/` files
7. Validate the structure matches the spec

## Quality checklist
- [ ] `name` matches directory name
- [ ] `name` follows naming rules (lowercase, hyphens, no leading/trailing hyphens)
- [ ] `description` is clear and includes activation keywords
- [ ] `SKILL.md` is under 500 lines
- [ ] References are one level deep from `SKILL.md`
- [ ] No deeply nested reference chains
- [ ] Instructions use active voice and are actionable

## References
See [spec details](references/agentskills-spec.md) for the full Agent Skills specification reference.

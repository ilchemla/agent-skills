# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Agent skills repository for Claude Code. Skills are stored in `skills/` with each skill in its own directory containing a `SKILL.md` manifest and optional `references/` directory for supporting documentation.

## Repository Structure

```
skills/
  <skill-name>/
    SKILL.md          # Skill manifest with YAML frontmatter
    references/       # Optional supporting documentation
```

## Skill Manifest Format (SKILL.md)

Each skill requires YAML frontmatter:

```yaml
---
name: skill-name
description: >
  Brief description of when to use this skill.
  Use when [specific scenarios].
---
```

**Key Requirements:**
- `name`: Kebab-case identifier
- `description`: Must include "Use when" clause describing invocation scenarios
- Description should clearly specify trigger conditions for Claude Code to auto-invoke the skill

## Current Skills

**qodo-pr-resolver**: Structured 3-phase workflow (Analyze → Confirm → Execute) for processing Qodo PR review comments with severity-based prioritization, multi-issue detection, and automatic thread resolution.

## Adding New Skills

1. Create `skills/<skill-name>/` directory
2. Add `SKILL.md` with required frontmatter and documentation
3. Include detailed workflow, prerequisites, and usage examples
4. Add `references/` subdirectory for supporting docs if needed
5. Commit with conventional commit format: `feat: add <skill-name> skill`

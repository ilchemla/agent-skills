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

**panel**: End-of-task review by 3-6 expert subagents picked for the work (code, docs, plans, messaging, slides, diagrams). Renders visual artifacts to images before review. Verifies findings, returns a P0/P1/P2 report with a ship / fix-first / rethink verdict, applies fixes only after approval. User state lives in `~/.claude/panel/`, never in the skill folder.

**tldr**: Bottom line of a long reply, plain-words explanations, and open questions one at a time. Optional always-on mode through a `UserPromptSubmit` hook (off by default). Learnings live in `~/.claude/tldr/`.

## Adding New Skills

1. Create `skills/<skill-name>/` directory
2. Add `SKILL.md` with required frontmatter and documentation
3. Include detailed workflow, prerequisites, and usage examples
4. Add `references/` subdirectory for supporting docs if needed
5. Commit with conventional commit format: `feat: add <skill-name> skill`

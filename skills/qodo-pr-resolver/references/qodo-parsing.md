# Qodo Comment Parsing Guide

Reference for parsing Qodo PR Agent comments. Read this during Phase 1 (Analyze) when fetching and parsing comment data.

## Two Comment Types

Qodo posts comments in **two locations**:

1. **General Comment** (Summary) - Contains all issues in one comment on the PR conversation
2. **Inline Comments** - Individual comments on specific code lines

You must fetch **both** to get all issues. The general comment often contains issues not found in inline comments.

## Fetching Comments

**General Comments** (via Issues API):
```bash
gh api repos/{owner}/{repo}/issues/{pr_number}/comments | jq '[.[] |
  select(.user.login == "qodo-code-review[bot]" or .user.login == "qodo-merge[bot]")
]'
```

**Inline Comments** (via Pulls API — filter out replies):
```bash
gh api repos/{owner}/{repo}/pulls/{pr_number}/comments | jq '[.[] |
  select(.user.login == "qodo-code-review[bot]" or .user.login == "qodo-merge[bot]") |
  select(.in_reply_to_id == null)
]'
```

## Parsing General Comments

General comments contain multiple issues in nested `<details>` blocks:

```html
<details><summary>1. Title <code>📘 Rule violation</code></summary>
  Description text...
  Code snippet...
  Evidence...
  <details><summary>Agent Prompt</summary>
    Fix instructions...
  </details>
</details>
```

- Each `<details>` block at the top level is a separate issue
- Extract file/line from GitHub links: `[app/file.py[R363-380]](https://github.com/...)`
- Parse all `<details>` sections to get the complete issue list

## Parsing Inline Comments

Simpler structure — one issue per comment:

- Metadata available: `.path`, `.line`, `.body`
- Body structure is similar to a single general comment `<details>` block
- May contain the same issues as the general comment (deduplicate by file+line+title)

## HTML Parsing

- Extract clean text from HTML using regex
- Parse `<details><summary>Agent Prompt</summary>` or `<summary>Agent prompt</summary>` for fix instructions
- Extract numbered items: `1. Title 📘 Rule violation ✓ Correctness`
- Look for **Fix Focus Areas** section for file:line locations

## Agent Prompt Extraction

Qodo provides ready-to-use fix prompts inside collapsible sections:

```html
<details><summary>Agent Prompt</summary>
  Issue description...
  Issue Context...
  Fix Focus Areas...
</details>
```

Extract these and use as primary fix guidance — they contain the issue description, context, and specific file:line locations to change.

## Severity Detection from Badges

Qodo uses emoji badges to indicate issue type:

| Badge | Meaning | Default Severity |
|-------|---------|-----------------|
| ⛨ Security | Security issue | CRITICAL (always) |
| 🐞 Bug + security context | Security bug | CRITICAL |
| 🐞 Bug | Functional bug | HIGH |
| ⛯ Reliability | Reliability issue | HIGH |
| 📘 Rule violation | Code rule violation | MEDIUM |
| ✓ Correctness | Correctness issue | MEDIUM |
| 📎 Requirement gaps | Minor gap | LOW (or MEDIUM depending on context) |

## Deduplication

The same issue often appears in both the general comment and an inline comment. Deduplicate by:

- `file:line:title` match
- `description_similarity` (fuzzy match on description text)

When duplicated, prefer the inline comment (it has better metadata like `.path` and `.line`), but track both comment IDs so you can resolve both threads later.

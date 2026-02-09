---
name: qodo-pr-resolver
description: >
  Resolve Qodo PR review comments through analyze-confirm-execute workflow with severity-based prioritization.
  Analyzes comment validity, detects CI failures, confirms response approach with user, executes code changes, runs tests, and resolves threads.
  Use when responding to Qodo PR review comments, addressing Qodo feedback, resolving review issues, or managing Qodo review threads.
---

# Qodo PR Resolver

Efficiently process PR review comments from Qodo PR Agent through a structured 3-phase workflow: **Analyze → Confirm → Execute**.

## Key Features

- 🎯 **Severity-based prioritization** (CRITICAL → HIGH → MEDIUM → LOW)
- 🧪 **Automatic test integration** and CI check fixing
- 📦 **Smart commit strategy** (functional vs cosmetic separation)
- 💬 **Standardized reply templates**
- ✅ **Automatic thread resolution** via GitHub API
- 🔍 **Multi-issue comment detection** and verification
- 🔄 **Fresh data verification** for completion

## When to Use

Use this skill when:
- Responding to Qodo PR Agent review comments on GitHub
- Addressing automated code review feedback
- Managing multiple review threads efficiently
- Need to validate comment relevance before acting
- Want structured approach to handling PR feedback with severity prioritization

## Prerequisites

**GitHub CLI Required:**

```bash
# Check installation
gh --version

# Authenticate if needed
gh auth login
```

## Critical Constraints

**⚠️ IMPORTANT:**
- Only **unresolved comments** are processed (resolved comments are skipped)
- **Phase 2 (Confirm) MUST run in parent process** - never use AskUserQuestion in sub-agents
- **CRITICAL/HIGH fixes require passing tests** - cannot skip
- **All sub-issues** in multi-issue comments must be addressed
- **Fresh verification** confirms zero unresolved items before completion

## 3-Phase Workflow

### Phase 1: ANALYZE (Parallel Sub-agents)

**Step 1: Fetch Data**
- Get current PR number and details
- Fetch unresolved review comments from `qodo-code-review[bot]`
- Filter HTML content to extract clean issue descriptions
- Extract **Agent Prompt** sections (ready-to-use fix instructions)
- Fetch failing CI checks (lint, tests, format)

**Step 2: Parallel Analysis**
- Launch Task agent (subagent_type="general-purpose") for EACH comment/check
- Each agent analyzes:
  - **Extract Agent Prompt**: Parse `<details><summary>Agent Prompt</summary>` section from HTML
  - **Severity**: Detect from Qodo badges (🐞 ⛨ 📘) + keywords (see [Severity Guide](references/severity-guide.md))
  - **Multi-issue detection**: Check for multiple distinct issues in one comment
  - **Validity**: valid/invalid/partial based on Evidence section
  - **Context**: Read file:line from .path and .line fields, understand purpose
  - **Action**: fix/reply/defer/ignore
  - **Fix proposal**: Use Agent Prompt + Fix Focus Areas as primary guidance

**Step 3: Sort Results**
- Sort by severity: CRITICAL → HIGH → MEDIUM → LOW
- Group multi-issue comments
- Prepare structured summary

### Phase 2: CONFIRM (Parent Process Only)

**Present Analysis:**

Display comments grouped by severity:

```
🔴 CRITICAL Issues (2):
  Comment #1 (auth.py:156) [MULTI-ISSUE: 2 items]
  - SQL injection AND missing validation
  - Action: fix (Recommended)

🟡 HIGH Issues (1):
  Comment #2 (service.py:42)
  - Null pointer exception
  - Action: fix (Recommended)

🟢 MEDIUM Issues (1):
  Comment #3 (utils.py:18)
  - Performance optimization
  - Action: defer (Recommended)

⚪ LOW Issues (2):
  Comments #4-5 - Variable naming, docstrings
  - Action: fix (batch together)

CI Checks (2 failing):
  - Lint: ESLint errors
  - Tests: 2 failing tests
```

**Get Confirmation:**
- Use AskUserQuestion for each severity group
- Options: Apply fix, Reply to reviewer, Defer to issue, Ignore, Custom
- CRITICAL/HIGH default to "Apply fix (Recommended)"
- Allow multi-select for similar comments

### Phase 3: EXECUTE

**Step 1: Detect Configuration**
- Auto-detect test/lint/format commands from project config
- See [Test Integration Guide](references/test-integration.md)

**Step 2: Apply Fixes (By Severity)**
- Process CRITICAL → HIGH → MEDIUM → LOW
- For each fix:
  - Apply code changes
  - Verify all sub-issues addressed (for multi-issue comments)
  - Commit with appropriate strategy:
    - **CRITICAL/HIGH**: Individual commits
    - **MEDIUM/LOW**: Batch into single commit
- Use Conventional Commits format
- See [Commit Strategy Guide](references/commit-strategy.md)

**Step 3: Fix CI Checks**
- Run lint --fix, formatters
- Commit CI fixes separately

**Step 4: Run Tests**
- Execute detected test command
- **MUST pass** for CRITICAL/HIGH fixes
- Handle failures: retry/fix/skip/abort
- See [Test Integration Guide](references/test-integration.md)

**Step 5: Push Changes**
- Push all commits at once
- Verify push succeeded

**Step 6: Reply to Reviewers**
- Use standard templates for each comment:
  - **Fixed**: "Fixed in [hash]: description"
  - **Won't Fix**: "Won't fix: reason"
  - **By Design**: "By design: explanation"
  - **Deferred**: "Deferred to #issue: will address later"
  - **Acknowledged**: "Acknowledged: note"
- See [Reply Templates](references/reply-templates.md)

**Step 7: Resolve Threads**
- Mark each addressed thread as resolved via GitHub GraphQL API
- Skip if user selected "Ignore"

**Step 8: Fresh Verification**
- Re-fetch PR data
- Confirm zero unresolved comments
- Verify all CI checks passing
- Provide completion summary

## Severity Classification

| Severity | Qodo Indicators | Keywords | Priority | Commit |
|----------|-----------------|----------|----------|--------|
| **CRITICAL** | ⛨ Security, 🐞 Bug (security) | security, vulnerability, injection, XSS, SQL | Must fix first | Individual |
| **HIGH** | 🐞 Bug, ⛯ Reliability | bug, error, crash, fail, memory leak | Should fix | Individual |
| **MEDIUM** | 📘 Rule violation, ✓ Correctness | performance, refactor, code smell, rule violation | Recommended | Batch |
| **LOW** | 📎 Requirement gaps (minor) | style, nit, formatting, typo | Optional | Batch |

**Qodo-Specific Detection:**
- Parse HTML for emoji badges: `🐞 Bug`, `📘 Rule violation`, `⛨ Security`
- Extract severity from badge combinations
- Security badge (⛨) → Always CRITICAL
- Bug badge (🐞) → HIGH (or CRITICAL if security-related)

**Processing order**: CRITICAL → HIGH → MEDIUM → LOW

See [Severity Guide](references/severity-guide.md) for detailed classification rules.

## Qodo-Specific Handling

**Bot Username:**
```bash
# Filter for qodo-code-review[bot] specifically
gh api repos/{owner}/{repo}/pulls/{pr_number}/comments | jq '[.[] |
  select(.user.login == "qodo-code-review[bot]") |
  select(.resolved == false)
]'
```

**HTML Parsing:**
- Extract clean text from HTML using regex or HTML parser
- Parse `<details><summary>Agent Prompt</summary>` for fix instructions
- Extract numbered items: `1. Title 📘 Rule violation ✓ Correctness`
- Look for **Fix Focus Areas** section for file:line locations

**Severity Detection:**
- ⛨ Security badge → CRITICAL
- 🐞 Bug + Security context → CRITICAL
- 🐞 Bug → HIGH
- 📘 Rule violation → MEDIUM
- 📎 Requirement gaps → LOW (or MEDIUM depending on context)

**Agent Prompt Usage:**
- Qodo provides ready-to-use fix prompts in `<details><summary>Agent Prompt</summary>`
- Extract these and use as primary fix guidance
- Agent Prompt contains: Issue description, Issue Context, Fix Focus Areas

**Response Format:**
- Match user's response pattern:
  - `✅ **FIXED** in commit [hash]` - Description
  - `❌ **NOT APPLICABLE**` - Reasoning
  - `📋 **DEFERRED** to #issue` - Will address later

## Quick Example

```
/qodo-pr-resolver

→ Found 2 Qodo comments + 2 CI failures
→ Parsing HTML, extracting Agent Prompts...
→ Detected severities: 1 CRITICAL (⛨ Security), 1 MEDIUM (📘 Rule)
→ Analyzing in parallel...
→ Presenting by severity (CRITICAL first)
→ User confirms actions
→ Applying fixes using Agent Prompt guidance
→ Running tests ✓
→ Posting replies: "✅ **FIXED** in commit [hash]"
→ Resolving threads
→ Fresh verification: 0 unresolved ✓
→ Summary: 1 CRITICAL fixed, 1 MEDIUM deferred
```

## Reference Documentation

**Core Guides:**
- [Severity Classification Guide](references/severity-guide.md) - Detailed severity rules and examples
- [Reply Templates](references/reply-templates.md) - Standard professional response templates
- [Commit Strategy](references/commit-strategy.md) - Conventional Commits and batching strategy

**Technical References:**
- [GitHub API Reference](references/api-reference.md) - All `gh` CLI commands used
- [Test Integration](references/test-integration.md) - Test detection, execution, failure handling

**Advanced Usage:**
- [Troubleshooting Guide](references/troubleshooting.md) - Common issues and solutions
- [Advanced Usage](references/advanced-usage.md) - Custom filters, batch processing, integrations

## Best Practices

### Analysis Phase
- **Severity first**: Classify before recommending action
- **Detect multi-issue**: Look for "AND", "also", "additionally"
- **Parallel execution**: Launch all agents at once
- **Include CI checks**: Analyze failing checks alongside comments

### Confirmation Phase
- **Present by severity**: Show CRITICAL first, LOW last
- **Smart defaults**: CRITICAL/HIGH default to "Apply fix"
- **Group similar**: Batch related MEDIUM/LOW comments

### Execution Phase
- **Process by severity**: Fix CRITICAL first, LOW last
- **Verify multi-issue**: Confirm ALL sub-issues addressed
- **Test before push**: NEVER push failing tests
- **Use templates**: Consistent professional replies
- **Resolve threads**: Automate via API
- **Fresh verification**: Always re-fetch to confirm completion

## Important Notes

- This skill is designed specifically for Qodo PR Agent comments
- Can be adapted for other automated review tools by modifying bot username filter
- Always verify changes before pushing to ensure correctness
- Maintain professional tone in all reviewer interactions (no emojis in replies)
- The analyze phase is crucial - thorough exploration prevents incorrect fixes
- Test integration ensures changes don't break existing functionality
- Fresh verification provides confidence that all work is complete

## Integration with Other Skills

**Before:**
- `/cleanup` - Clean up code before review

**After:**
- `/create-ticket` - Create tickets for deferred items
- `/commit` - Additional commits if needed
- Verify: `gh pr checks` - All CI passing

See [Advanced Usage](references/advanced-usage.md) for complete workflow examples.

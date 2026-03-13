---
name: qodo-pr-resolver
description: >
  Resolve Qodo PR review comments through wait-analyze-confirm-execute workflow with severity-based prioritization.
  Auto-waits for Qodo review via polling if still generating, then analyzes comment validity, detects CI failures,
  confirms response approach with user, executes code changes, runs tests, and resolves threads.
  Use when responding to Qodo PR review comments, addressing Qodo feedback, resolving review issues, or managing Qodo review threads.
---

# Qodo PR Resolver

Efficiently process PR review comments from Qodo PR Agent through a structured 4-phase workflow: **Wait → Analyze → Confirm → Execute**.

## Key Features

- 🎯 **Severity-based prioritization** (CRITICAL → HIGH → MEDIUM → LOW)
- 🧪 **Automatic test integration** and CI check fixing
- 📦 **Smart commit strategy** (functional vs cosmetic separation)
- 💬 **Standardized reply templates**
- ✅ **Automatic thread resolution** via GitHub API
- 🔍 **Multi-issue comment detection** and verification
- 🔄 **Fresh data verification** for completion
- ⏳ **Auto-wait for Qodo review** via `/loop` polling when review is still generating

## When to Use

Use this skill when:
- Responding to Qodo PR Agent review comments on GitHub
- Addressing automated code review feedback
- Managing multiple review threads efficiently
- Need to validate comment relevance before acting
- Want structured approach to handling PR feedback with severity prioritization
- Just opened a PR and want to process Qodo's review as soon as it's ready

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
- **Phase 0 (Wait) uses CronCreate/CronDelete** — the cron job must self-delete once the review is detected
- **Phase 2 (Confirm) MUST run in parent process** - never use AskUserQuestion in sub-agents
- **CRITICAL/HIGH fixes require passing tests** - cannot skip
- **All sub-issues** in multi-issue comments must be addressed
- **Fresh verification** confirms zero unresolved items before completion

## 4-Phase Workflow

### Phase 0: WAIT FOR REVIEW (Loop-based Polling)

Qodo's review takes a few minutes to generate after a PR is opened. During this time, Qodo posts a placeholder comment containing "Looking for bugs?" / "An AI review agent is analyzing this pull request". The actual review replaces this placeholder once ready.

**Step 1: Check Review Readiness**
- Fetch Qodo bot comments on the PR:
  ```bash
  gh api repos/{owner}/{repo}/issues/{pr_number}/comments | jq '[.[] |
    select(.user.login == "qodo-code-review[bot]" or .user.login == "qodo-merge[bot]")
  ]'
  ```
- **Review is ready** if: Qodo comments exist AND none contain the placeholder text ("Looking for bugs?" or "An AI review agent is analyzing")
- **Review is NOT ready** if: No Qodo comments exist, OR comments contain the placeholder text

**Step 2: If Not Ready, Set Up Polling via `/loop`**
- Use CronCreate to schedule a polling job every 2 minutes:
  ```
  CronCreate with cron expression "*/2 * * * *" and prompt:
  "Check if Qodo review is ready on PR #{pr_number}. Fetch comments with:
   gh api repos/{owner}/{repo}/issues/{pr_number}/comments
   If Qodo's comment no longer contains 'Looking for bugs?' or 'An AI review agent is analyzing',
   the review is ready — delete this cron job (CronDelete) and run /qodo-pr-resolver to process it.
   If still not ready, report status and wait for next poll."
  ```
- Inform the user: "Qodo review is still generating. Polling every 2 minutes — you can keep working."
- **STOP here** — do not proceed to Phase 1. The cron job will re-invoke the skill when ready.

**Step 3: If Ready, Proceed Directly**
- Skip polling setup, proceed to Phase 1 immediately.

**Important Notes:**
- Cron jobs are **session-scoped** — they stop if you exit Claude Code
- Jobs **auto-expire after 3 days** as a safety net
- The cron job **must delete itself** (CronDelete) once the review is detected
- If Qodo takes unusually long (>10 minutes), the cron will keep polling — user can cancel manually via CronList + CronDelete

### Phase 1: ANALYZE (Parallel Sub-agents)

**Step 1: Fetch Data**
- Get current PR number and details
- Fetch **both types** of Qodo comments:
  - **General comments**: Summary comment with all issues (via `/repos/{owner}/{repo}/issues/{pr}/comments`)
  - **Inline comments**: Comments on specific lines (via `/repos/{owner}/{repo}/pulls/{pr}/comments`)
- Parse HTML to extract clean issue descriptions from both formats
- Extract **Agent Prompt** sections (ready-to-use fix instructions)
- Deduplicate issues that appear in both comment types
- Fetch failing CI checks (lint, tests, format)

**Step 2: Deduplicate Issues**
- Same issue may appear in both general and inline comments
- Deduplicate by: `file:line:title` or `description_similarity`
- Prefer inline comment if duplicate (has better metadata)
- Track both comment IDs for thread resolution

**Step 3: Parallel Analysis**
- Launch Task agent (subagent_type="general-purpose") for EACH unique issue/check
- Each agent analyzes:
  - **Extract Agent Prompt**: Parse `<details><summary>Agent Prompt</summary>` or `<summary>Agent prompt</summary>` section from HTML
  - **Severity**: Detect from Qodo badges (🐞 ⛨ 📘) + keywords (see [Severity Guide](references/severity-guide.md))
  - **Multi-issue detection**: For general comments, each `<details>` block is separate issue
  - **Validity**: valid/invalid/partial based on Evidence section
  - **Context**: Read file:line from metadata (inline) or GitHub links (general), understand purpose
  - **Action**: fix/reply/defer/ignore
  - **Fix proposal**: Use Agent Prompt + Fix Focus Areas as primary guidance

**Step 4: Sort Results**
- Sort by severity: CRITICAL → HIGH → MEDIUM → LOW
- Group related issues from same file
- Prepare structured summary with both general and inline comment IDs

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
- Reply to **all comment locations** where issue appears:
  - If issue is in general comment: Reply to that comment
  - If issue is in inline comment: Reply to that inline thread
  - If issue appears in both: Reply to both locations with same message
- Use standard templates for each comment:
  - **Fixed**: "Fixed in [hash]: description"
  - **Won't Fix**: "Won't fix: reason"
  - **By Design**: "By design: explanation"
  - **Deferred**: "Deferred to #issue: will address later"
  - **Acknowledged**: "Acknowledged: note"
- See [Reply Templates](references/reply-templates.md)

**Step 7: Resolve Threads**
- Mark each addressed thread as resolved via GitHub GraphQL API
- For issues in both locations, resolve both threads
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

**Two Comment Types:**

Qodo posts comments in **two locations**:

1. **General Comment** (Summary) - Contains all issues in one comment on the PR conversation
2. **Inline Comments** - Individual comments on specific code lines

**IMPORTANT**: You must fetch **both** to get all issues. General comment often contains issues not in inline comments.

**Fetch General Comments:**
```bash
# General PR comments (summary with all issues)
gh api repos/{owner}/{repo}/issues/{pr_number}/comments | jq '[.[] |
  select(.user.login == "qodo-code-review[bot]" or .user.login == "qodo-merge[bot]")
]'
```

**Fetch Inline Comments:**
```bash
# Inline code review comments (specific lines)
gh api repos/{owner}/{repo}/pulls/{pr_number}/comments | jq '[.[] |
  select(.user.login == "qodo-code-review[bot]" or .user.login == "qodo-merge[bot]") |
  select(.in_reply_to_id == null)
]'
```

**Parse General Comments:**
- General comment contains multiple issues in nested `<details>` blocks
- Structure: `<details><summary>1. Title <code>📘 Rule violation</code></summary>` (collapsed sections)
- Each issue has: Description, Code snippet, Evidence, Agent Prompt
- Extract file/line from GitHub links: `[app/file.py[R363-380]](https://github.com/...)`
- Parse all `<details>` sections to get complete issue list

**Parse Inline Comments:**
- Simpler structure with single issue per comment
- Metadata available: `.path`, `.line`, `.body`
- May contain same issues as general comment (deduplicate by file+line+title)

**HTML Parsing:**
- Extract clean text from HTML using regex or HTML parser
- Parse `<details><summary>Agent Prompt</summary>` or `<summary>Agent prompt</summary>` for fix instructions
- Extract numbered items: `1. Title 📘 Rule violation ✓ Correctness`
- Look for **Fix Focus Areas** section for file:line locations
- For general comments: Parse multiple `<details>` blocks to extract all issues

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

## Quick Examples

**Example 1: Review already ready**
```
/qodo-pr-resolver

→ Checking Qodo review status... Review is ready!
→ Fetching general comments... Found 1 (with 2 issues)
→ Fetching inline comments... Found 1
→ Deduplicating... 2 unique issues total
→ Parsing HTML, extracting Agent Prompts...
→ Detected severities: 1 HIGH (📘 ⛯ Reliability), 1 MEDIUM (📘 ✓ Correctness)
→ Analyzing in parallel...
→ Presenting by severity (HIGH first)
→ User confirms actions
→ Applying fixes using Agent Prompt guidance
→ Running tests ✓
→ Posting replies to both general and inline comments
→ Resolving threads (2 resolved)
→ Fresh verification: 0 unresolved ✓
→ Summary: 1 HIGH fixed, 1 MEDIUM deferred
```

**Example 2: Review still generating (polling)**
```
/qodo-pr-resolver

→ Checking Qodo review status... Still generating ("Looking for bugs?")
→ Setting up polling every 2 minutes...
→ Cron job created. You can keep working — I'll notify you when the review is ready.

  [2 minutes later - cron fires]
→ Polling... Qodo review still generating.

  [2 more minutes - cron fires]
→ Polling... Review is ready! Deleting cron job.
→ Running /qodo-pr-resolver...
→ [Proceeds with Phase 1: Analyze → Confirm → Execute]
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

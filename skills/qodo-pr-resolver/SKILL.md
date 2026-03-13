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

### Pre-check: Verify Code is Pushed

Before anything else, check that the user's local code matches what Qodo reviewed on the remote. Qodo reviews what's on the remote branch, so local-only changes would make you fix stale comments.

```bash
git status --porcelain     # Check for uncommitted changes
git log @{u}..HEAD --oneline  # Check for unpushed commits
```

- **Uncommitted changes exist**: Inform the user and ask if they want to commit and push first.
- **Unpushed commits exist**: Inform the user that Qodo hasn't reviewed these yet. Ask if they want to push. If yes, push and tell them to wait ~5 minutes for Qodo to re-review, then re-run the skill.
- **Everything pushed**: Proceed to Phase 0.

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
  "Check if Qodo review is ready on PR #<actual_number> in <actual_owner>/<actual_repo>.
   Fetch comments with: gh api repos/<actual_owner>/<actual_repo>/issues/<actual_number>/comments
   If Qodo's comment no longer contains 'Looking for bugs?' or 'An AI review agent is analyzing',
   the review is ready — delete this cron job (CronDelete) and run /qodo-pr-resolver to process it.
   If still not ready, report status and wait for next poll."
  NOTE: Replace all placeholders with actual resolved values before creating the cron.
  The cron fires in a fresh context with no memory of prior variables.
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

**Step 1: Detect PR Context (Parent Process)**
- Get the current PR number and repo info:
  ```bash
  gh pr view --json number,headRepositoryOwner,headRepository -q '{number: .number, owner: .headRepositoryOwner.login, repo: .headRepository.name}'
  ```
- Store `pr_number`, `owner`, and `repo` — these are used in all subsequent API calls

**Step 2: Fetch and Deduplicate (Parent Process)**

This step runs in the parent process because it produces the issue list that gets distributed to sub-agents.

- Fetch **both types** of Qodo comments (see [Qodo Parsing Guide](references/qodo-parsing.md) for exact API calls and HTML parsing details):
  - **General comments**: Summary comment with all issues (via Issues API)
  - **Inline comments**: Comments on specific lines (via Pulls API)
- Parse HTML to extract clean issue descriptions from both formats
- Extract **Agent Prompt** sections (ready-to-use fix instructions)
- Deduplicate issues that appear in both comment types (by `file:line:title`)
- Prefer inline comment if duplicate (has better metadata), but track both comment IDs
- Fetch failing CI checks (lint, tests, format)

**Step 3: Parallel Analysis (via Sub-agents)**

Each unique issue gets its own sub-agent so they all run in parallel. This matters because a PR with 5+ issues would take forever to analyze sequentially, but finishes in the time of the slowest single analysis when parallelized.

For each unique issue/check from Step 2, launch a sub-agent using the Agent tool:

```
Agent(
  subagent_type="general-purpose",
  description="Analyze Qodo issue: <short title>",
  prompt="""
  Analyze this Qodo PR review issue and return a structured assessment.

  ## Issue Data
  - Title: <issue title>
  - File: <file path>
  - Line(s): <line range>
  - Raw HTML body: <the comment body or details block>
  - Comment ID(s): <general comment ID and/or inline comment ID>

  ## Your Tasks
  1. Extract the Agent Prompt section from the HTML (look for <details><summary>Agent Prompt</summary> or <summary>Agent prompt</summary>)
  2. Read the referenced file and lines to understand the code context
  3. Classify severity using Qodo badges: ⛨ Security → CRITICAL, 🐞 Bug → HIGH, 📘 Rule → MEDIUM, 📎 Minor → LOW
  4. Assess validity: is this a real issue (valid), false positive (invalid), or partially correct (partial)?
  5. Check for multi-issue: does this comment contain multiple distinct problems?
  6. Recommend action: fix / reply / defer / ignore

  ## Return Format
  Return your analysis as a structured summary:
  - severity: CRITICAL | HIGH | MEDIUM | LOW
  - validity: valid | invalid | partial
  - action: fix | reply | defer | ignore
  - sub_issues: [list if multi-issue, otherwise single item]
  - agent_prompt: <extracted agent prompt text>
  - fix_proposal: <what to change and why>
  - comment_ids: {general: <id or null>, inline: <id or null>}
  """
)
```

Launch ALL sub-agents in a single message (multiple Agent tool calls in one response) so they run concurrently. Do not wait for one to finish before launching the next.

**Step 4: Collect Results (Preserve Qodo's Order)**
- Wait for all sub-agents to return
- Preserve Qodo's original ordering — do not re-sort by severity. Qodo already orders issues by importance, and re-sorting can lose that intent.
- Annotate each issue with its severity classification from the sub-agent analysis
- Prepare structured summary with both general and inline comment IDs

### Phase 2: CONFIRM (Parent Process Only)

This phase is a hard gate — you cannot proceed to Phase 3 without explicit user approval. The user needs to see what was found and decide what to do about each group before any code is changed. This prevents unwanted fixes and gives the user control over the response strategy.

**Step 1: Present Analysis**

Display issues in Qodo's original order, annotated with severity:

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

**Step 2: Get User Confirmation via AskUserQuestion**

After presenting the analysis above, use the AskUserQuestion tool to ask the user what to do. This is not optional — do not skip this and jump to fixing.

Use AskUserQuestion for each severity group that has issues. Example:

```
AskUserQuestion(
  question="""
  How would you like to handle the CRITICAL issues?

  1. Comment #1 (auth.py:156) - SQL injection + missing validation
     Recommended: Apply fix

  Options per issue:
  - fix: Apply the recommended code change
  - reply: Reply to reviewer explaining why (no code change)
  - defer: Create a ticket and reply with "Deferred to #issue"
  - ignore: Skip entirely (no reply, no fix)

  Reply with your choice for each issue (e.g., "fix all" or "fix #1, defer #2").
  """
)
```

Then ask again for HIGH issues, then MEDIUM, then LOW. You can batch MEDIUM and LOW into one question if there are many:

```
AskUserQuestion(
  question="""
  How would you like to handle the remaining MEDIUM/LOW issues?

  MEDIUM:
  3. Comment #3 (utils.py:18) - Performance optimization → Recommended: defer

  LOW:
  4. Comment #4 (helpers.py:5) - Variable naming → Recommended: fix (batch)
  5. Comment #5 (helpers.py:22) - Missing docstring → Recommended: fix (batch)

  Reply with your choices (e.g., "defer #3, fix #4-5").
  """
)
```

Wait for each AskUserQuestion response before proceeding. Only after ALL severity groups are confirmed, move to Phase 3.

**Defaults when user says "go ahead" or similar:**
- CRITICAL/HIGH: Apply fix
- MEDIUM: Defer
- LOW: Fix (batched)

### Phase 3: EXECUTE

**Step 1: Detect Configuration**
- Auto-detect test/lint/format commands from project config
- See [Test Integration Guide](references/test-integration.md)

**Step 2: Fix → Commit → Reply → Resolve (Per Issue)**

Process each issue individually in Qodo's original order. For each fix, the full cycle is: apply code change → commit → reply to thread → resolve thread. This keeps git history clean (one commit per fix) and closes threads as you go.

For each issue the user approved as "fix":
1. **Apply** the code change using the Agent Prompt as primary guidance
2. **Verify** all sub-issues addressed (for multi-issue comments)
3. **Commit** with Conventional Commits format: `fix: <issue title>` (see [Commit Strategy Guide](references/commit-strategy.md))
4. **Reply** to all comment locations where this issue appears (inline thread and/or general comment) using templates from [Reply Templates](references/reply-templates.md)
5. **Resolve** the thread(s) via GitHub GraphQL API

For deferred issues, reply with the deferral reason and resolve the thread — no code change or commit needed.

Skip issues the user selected "Ignore" — no reply, no resolve.

**Step 3: Fix CI Checks**
- Run lint --fix, formatters
- Commit CI fixes separately: `style: fix lint/formatting issues`

**Step 4: Run Tests**
- Execute detected test command
- **MUST pass** for CRITICAL/HIGH fixes
- Handle failures: retry/fix/skip/abort
- See [Test Integration Guide](references/test-integration.md)

**Step 5: Push Changes**
- Push all commits at once
- Verify push succeeded

**Step 6: React to Qodo's Review Comment**
- Find Qodo's main "Code Review by Qodo" comment and add a +1 reaction to acknowledge it:
  ```bash
  gh api repos/{owner}/{repo}/issues/comments/{qodo_comment_id}/reactions \
    -X POST -f content='+1'
  ```
- If the reaction fails (comment not found, API error), continue — this is a nice-to-have, not critical.

**Step 7: Fresh Verification**
- Re-fetch PR data
- Confirm zero unresolved comments
- Verify all CI checks passing
- Provide completion summary

**Step 8: Show PR URL**
- Print the PR link so the user can navigate to it:
  ```
  PR: https://github.com/{owner}/{repo}/pull/{pr_number}
  ```

## Severity Classification

| Severity | Qodo Indicators | Keywords | Priority |
|----------|-----------------|----------|----------|
| **CRITICAL** | ⛨ Security, 🐞 Bug (security) | security, vulnerability, injection, XSS, SQL | Must fix first |
| **HIGH** | 🐞 Bug, ⛯ Reliability | bug, error, crash, fail, memory leak | Should fix |
| **MEDIUM** | 📘 Rule violation, ✓ Correctness | performance, refactor, code smell, rule violation | Recommended |
| **LOW** | 📎 Requirement gaps (minor) | style, nit, formatting, typo | Optional |

**Processing order**: CRITICAL → HIGH → MEDIUM → LOW

For Qodo badge-to-severity mapping, see [Qodo Parsing Guide](references/qodo-parsing.md). For detailed classification rules, see [Severity Guide](references/severity-guide.md).

## Qodo-Specific Handling

For detailed parsing instructions (API calls, HTML structure, badge detection, deduplication), see the [Qodo Parsing Guide](references/qodo-parsing.md). Read it during Phase 1 Step 2 when fetching and parsing comment data.

**Key points:**
- Qodo posts in **two locations** (general summary + inline comments) — fetch both
- Deduplicate by `file:line:title` before launching sub-agents
- Extract Agent Prompt sections as primary fix guidance
- Use Qodo reply format for responses (see [Reply Templates](references/reply-templates.md))

## Quick Examples

**Example 1: Review already ready**
```
/qodo-pr-resolver

→ Pre-check: All code pushed ✓

→ Phase 0: Checking Qodo review status... Review is ready!

→ Phase 1: Fetching general comments... Found 1 (with 2 issues)
→ Phase 1: Fetching inline comments... Found 1
→ Phase 1: Deduplicating... 2 unique issues total
→ Phase 1: Launching 2 sub-agents in parallel to analyze each issue...
→ Phase 1: All sub-agents complete. Issues annotated with severity.

→ Phase 2: Presenting issues in Qodo's order...
   [displays issue table with severity annotations]
→ Phase 2: AskUserQuestion — "How to handle HIGH issues? (fix/reply/defer/ignore)"
   User: "fix"
→ Phase 2: AskUserQuestion — "How to handle MEDIUM issues? (fix/reply/defer/ignore)"
   User: "defer"

→ Phase 3: Fix #1 (HIGH) → commit → reply → resolve ✓
→ Phase 3: Defer #2 (MEDIUM) → reply → resolve ✓
→ Phase 3: Running tests ✓
→ Phase 3: Pushing all commits...
→ Phase 3: +1 reaction on Qodo's review comment ✓
→ Phase 3: Fresh verification: 0 unresolved ✓
→ Summary: 1 HIGH fixed, 1 MEDIUM deferred
→ PR: https://github.com/owner/repo/pull/123
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
- [Qodo Parsing Guide](references/qodo-parsing.md) - Comment fetching, HTML parsing, badge detection, deduplication
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
- **One sub-agent per issue**: Each Qodo issue gets its own Agent(subagent_type="general-purpose") call — never analyze issues inline in the parent process
- **Launch all at once**: Put all Agent tool calls in a single response so they run concurrently
- **Pass full context**: Each sub-agent needs the raw HTML body, file path, line range, and comment IDs
- **Severity first**: Classify before recommending action
- **Detect multi-issue**: Look for "AND", "also", "additionally"
- **Include CI checks**: Analyze failing checks alongside comments

### Confirmation Phase
- **Always use AskUserQuestion**: Never skip confirmation — this is a hard gate before Phase 3
- **Ask per severity group**: One AskUserQuestion for CRITICAL, one for HIGH, one for MEDIUM/LOW (can batch)
- **Wait for each response**: Do not proceed to the next group until the user answers
- **Present by severity**: Show CRITICAL first, LOW last
- **Smart defaults**: If user says "go ahead" → CRITICAL/HIGH=fix, MEDIUM=defer, LOW=fix(batch)
- **Group similar**: Batch related MEDIUM/LOW comments into one question

### Execution Phase
- **One commit per fix**: Apply → commit → reply → resolve for each issue before moving to the next
- **Preserve Qodo's order**: Process issues in Qodo's original order, not re-sorted by severity
- **Verify multi-issue**: Confirm ALL sub-issues addressed
- **Test before push**: NEVER push failing tests
- **Use templates**: Consistent professional replies
- **React to review**: Add +1 reaction to Qodo's main comment
- **Show PR URL**: Print the PR link at the end
- **Fresh verification**: Always re-fetch to confirm completion

## Important Notes

- This skill is designed specifically for Qodo PR Agent comments
- Can be adapted for other automated review tools by modifying bot username filter
- Always verify changes before pushing to ensure correctness
- Maintain professional tone in all reviewer interactions (use Qodo emoji format for Qodo comments, see [Reply Templates](references/reply-templates.md))
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

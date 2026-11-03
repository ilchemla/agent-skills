---
name: qodo-pr-resolver
description: >
  Resolve Qodo PR review findings through wait-analyze-confirm-execute workflow with severity-based prioritization.
  Reads findings as structured JSON through the Qodo CLI (falls back to GitHub comments), checks the review is at
  the PR head, analyzes each finding in parallel, confirms the approach with the user, fixes with one commit per
  finding, runs tests, and records outcomes in Qodo. Use when responding to Qodo PR review comments, addressing
  Qodo feedback, resolving review issues, or managing Qodo review threads on your own PR. Supersedes
  qodo:qodo-review-resolver for that job.
---

# Qodo PR Resolver

Efficiently process PR review comments from Qodo PR Agent through a structured 4-phase workflow: **Wait → Analyze → Confirm → Execute**.

## Key Features

- 🎯 **Severity-based prioritization** (CRITICAL → HIGH → MEDIUM → LOW)
- 🧪 **Automatic test integration** and CI check fixing
- 📦 **Smart commit strategy** (functional vs cosmetic separation)
- 💬 **Standardized reply templates**
- 🧾 **Structured findings** from Qodo's own record (`qodo read pr-review-session findings`), not scraped HTML
- 🎯 **Head-SHA freshness**: works only on a review of the code that is actually on the PR
- ✅ **Outcomes recorded in Qodo** (`mark-implemented` / `dismiss`), which also resolves the PR threads and clears the merge block
- 🔍 **Multi-issue detection** and verification
- 🔄 **Fresh data verification** for completion
- ⏳ **Auto-wait for Qodo review** via cron polling when review is still generating

## Prerequisites

**GitHub CLI Required:**

```bash
# Check installation
gh --version

# Authenticate if needed
gh auth login
```

**Qodo CLI 2.0+ (recommended):**

```bash
qodo --version                                         # must be 2.0.0 or newer
qodo read whoami --json                                # logged in?
```

Choose the **data path** once, at Phase 0:
- **Structured path**: `qodo --version` is 2.0+, `whoami` succeeds, and
  `qodo read pr-review-session findings --pr-url <url> --json` returns JSON. Use it everywhere below.
- **Fallback path**: any of those fails (CLI missing or older than 2.0, logged out, or the repo is not in
  your Qodo workspace). Use the GitHub-comment path in [Qodo Parsing Guide](references/qodo-parsing.md).
  Say which path you took and why. A CLI older than 2.0 is an "upgrade the Qodo CLI" problem, not a login
  problem: `qodo update` stays inside a major version, so 1.x to 2.x needs Qodo's checksum-pinned installer
  (the `qodo:qodo-setup` skill has it).

Run `qodo` commands from a directory outside the repo and keep stderr out of the JSON (`2>/dev/null`):
it prints a trace line.

## Critical Constraints

**⚠️ IMPORTANT:**
- Only **open findings** are processed (`attribution_status` open, or unresolved threads on the fallback path)
- **Only a review at the PR head counts**: `review_session.status == "completed"` and `commit_sha` equals the PR's `headRefOid`
- **Qodo write tools need explicit approval**: `mark-implemented` and `dismiss` change Qodo's record and the PR; run them only for the outcomes the user approved in Phase 2
- **Phase 0 (Wait) uses CronCreate/CronDelete**: the cron job must self-delete once the review is detected
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
- **Unpushed commits exist**: Inform the user that Qodo hasn't reviewed these yet. Ask if they want to push. If yes, push, trigger a re-review (Phase 3, Step 9), and wait for it as in Phase 0.
- **Everything pushed**: Proceed to Phase 0.

**Checkout binding.** Before editing anything, check that this checkout is the PR you are fixing: the
PR's `owner/repo` (from its URL) matches the local `origin` remote, and local `HEAD` equals the PR's
`headRefOid`. If either differs, stop and say so rather than fixing a different tree.

### Phase 0: WAIT FOR REVIEW (Loop-based Polling)

Qodo's review takes a few minutes to generate after a PR is opened.

**Step 1: Check Review Readiness**

*Structured path:* read `review_session` from
`qodo read pr-review-session findings --pr-url <url> --json`:

| `review_session` | Meaning | Action |
|---|---|---|
| `null` | No review yet | Not ready: poll (Step 2), or trigger one (Step 9 trigger) if none is coming |
| `status: started` | Running | Not ready: poll |
| `status: completed`, `commit_sha` == PR `headRefOid` | Fresh | Ready: Phase 1 |
| `status: completed`, other `commit_sha` | Stale (a push since) | Not ready: trigger a re-review (Phase 3, Step 9) and poll |
| `failed`, `aborted`, `skipped`, `superseded` | No usable review | Tell the user; trigger once, then poll |

Compare SHAs against the PR's `headRefOid` from `gh pr view`, never local `HEAD` alone. A result with
`qar_operation_result_truncated` is incomplete: say so and do not treat it as clean.

*Fallback path:* Qodo posts a placeholder comment containing "Looking for bugs?" / "An AI review agent
is analyzing this pull request" while it works, and replaces it once ready.
- Fetch Qodo bot comments on the PR:
  ```bash
  gh api repos/{owner}/{repo}/issues/{pr_number}/comments | jq '[.[] |
    select(.user.login == "qodo-code-review[bot]" or .user.login == "qodo-merge[bot]")
  ]'
  ```
- **Review is ready** if: Qodo comments exist AND none contain the placeholder text ("Looking for bugs?" or "An AI review agent is analyzing") AND the latest Qodo review comment names the PR's `headRefOid` (full or short SHA). If it names an older SHA, the review is stale: trigger a re-review (Phase 3, Step 9)
- **After a re-review trigger** (Phase 3, Step 9): use Step 9's stricter rule instead, so the previous review is not mistaken for the new one.
- **Review is NOT ready** if: No Qodo comments exist, OR comments contain the placeholder text

**Step 2: If Not Ready, Set Up Polling via `/loop`**
- Use CronCreate to schedule a polling job every 2 minutes:
  ```
  CronCreate with cron expression "*/2 * * * *" and prompt:
  "Check if Qodo review is ready on PR #<actual_number> in <actual_owner>/<actual_repo>.
   Structured path: run `qodo read pr-review-session findings --pr-url <actual_url> --json 2>/dev/null`
   from outside the repo; ready when review_session.status is completed and commit_sha equals
   `gh pr view <actual_url> --json headRefOid -q .headRefOid`.
   Fallback path: fetch gh api repos/<actual_owner>/<actual_repo>/issues/<actual_number>/comments;
   ready when Qodo's comment no longer contains 'Looking for bugs?' or 'An AI review agent is analyzing'
   and that comment names <actual_head_sha>.
   When ready: delete this cron job (CronDelete) and run /qodo-pr-resolver to process it.
   Stop if review_session.status is failed, aborted, skipped or superseded, or 20 minutes have passed since
   <actual_start_time> with no ready review at head: delete this cron (CronDelete), report the state and the PR link.
   If still not ready, report status and wait for next poll."
  NOTE: Replace all placeholders with actual resolved values before creating the cron.
  The cron fires in a fresh context with no memory of prior variables.
  ```
- Inform the user: "Qodo review is still generating. Polling every 2 minutes. You can keep working."
- **STOP here**: do not proceed to Phase 1. The cron job will re-invoke the skill when ready.

**Step 3: If Ready, Proceed Directly**
- Skip polling setup, proceed to Phase 1 immediately.

Cron jobs are session-scoped and expire after 3 days; the job must delete itself once the review is ready.

### Phase 1: ANALYZE (Parallel Sub-agents)

**Step 1: Detect PR Context (Parent Process)**
- Get the current PR number and repo info:
  ```bash
  gh pr view --json number,url -q '{number: .number, url: .url, owner: (.url | split("/")[3]), repo: (.url | split("/")[4])}'
  ```
- Store `pr_number`, `pr_url`, `owner`, and `repo`: these are used in all subsequent API calls. They come from the PR's own URL, so they name the base repository even when the PR comes from a fork (the head repository's owner and name would point at the fork).

**Step 2: Fetch and Deduplicate (Parent Process)**

This step runs in the parent process because it produces the issue list that gets distributed to sub-agents.

*Structured path:*
```bash
qodo read pr-review-session findings --pr-url <url> --json 2>/dev/null
qodo read pr-review-session findings --pr-url <url> --extended --json 2>/dev/null  # code snippet + evidence explanation
```
- Each finding comes once, with `id`, `title`, `description`, `category`, `action_level`
  (`action_required` > `remediation_recommended` > `informational`), `attribution_status`, `git_sha`,
  `location` (`file_path`, `start_line`, `end_line`, `side`) and `evidence.citations`. No dedup needed.
- Keep only open findings (skip `implemented` and dismissed ones). Current findings can come from runs
  earlier than `review_session`: keep them, they are still open.
- The finding `id` is the key for Phase 3 outcomes. There are no GitHub comment IDs and no fix
  instructions in this record: the fix is chosen from the description, location and evidence.
- Use `--extended` when a finding is unclear: it adds `location.code_snippet` and `evidence.explanation`.

*Fallback path:* fetch **both types** of Qodo comments (see [Qodo Parsing Guide](references/qodo-parsing.md) for exact API calls and HTML parsing details):
  - **General comments**: Summary comment with all issues (via Issues API)
  - **Inline comments**: Comments on specific lines (via Pulls API)
- Parse HTML to extract clean issue descriptions from both formats
- Extract **Agent Prompt** sections (ready-to-use fix instructions)
- Deduplicate issues that appear in both comment types (by `file:line:title`)
- Prefer inline comment if duplicate (has better metadata), but track both comment IDs

Both paths: fetch failing CI checks (lint, tests, format).

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
  - Structured path: finding id, category, action_level, description, evidence.citations
    (and code_snippet / evidence.explanation if read with --extended)
  - Fallback path: raw HTML body and comment ID(s) (general and/or inline)

  ## Your Tasks
  1. Fallback path only: extract the Agent Prompt section from the HTML (look for <details><summary>Agent Prompt</summary> or <summary>Agent prompt</summary>)
  2. Read the referenced file and lines, and each cited source, to understand the code context.
     The citations are Qodo's claim to test, not proof.
  3. Classify severity: structured path from category + action_level (see Severity Classification);
     fallback path from badges: ⛨ Security → CRITICAL, 🐞 Bug → HIGH, 📘 Rule → MEDIUM, 📎 Minor → LOW
  4. Assess validity: is this a real issue (valid), false positive (invalid), or partially correct (partial)?
  5. Check for multi-issue: does this finding contain multiple distinct problems?
  6. Recommend action: fix / reply / defer / ignore

  ## Return Format
  Return your analysis as a structured summary:
  - severity: CRITICAL | HIGH | MEDIUM | LOW
  - validity: valid | invalid | partial
  - action: fix | reply | defer | ignore
  - sub_issues: [list if multi-issue, otherwise single item]
  - agent_prompt: <extracted agent prompt text, fallback path only>
  - fix_proposal: <what to change and why>
  - finding_id: <Qodo finding id, structured path> | comment_ids: {general, inline} (fallback path)
  """
)
```

Launch ALL sub-agents in a single message (multiple Agent tool calls in one response) so they run concurrently. Do not wait for one to finish before launching the next.

**Step 4: Collect Results (Preserve Qodo's Order)**
- Wait for all sub-agents to return
- Preserve Qodo's original ordering: do not re-sort by severity. Qodo already orders issues by importance, and re-sorting can lose that intent.
- Annotate each issue with its severity classification from the sub-agent analysis
- Prepare structured summary keyed by finding ID (structured path) or comment IDs (fallback path)

### Phase 2: CONFIRM (Parent Process Only)

This phase is a hard gate: you cannot proceed to Phase 3 without explicit user approval. The user needs to see what was found and decide what to do about each group before any code is changed. This prevents unwanted fixes and gives the user control over the response strategy.

**Step 1: Present Analysis**

Display issues in Qodo's original order, one line each: severity, `file:line`, title, multi-issue count,
recommended action (fix / reply / defer / ignore). Then failing CI checks, one line each.

**Step 2: Get User Confirmation via AskUserQuestion**

After presenting the analysis above, use the AskUserQuestion tool to ask the user what to do. This is not optional: do not skip this and jump to fixing.

Ask **one** AskUserQuestion with `multiSelect: true`: "Which findings should I fix?" One option per
finding (up to 4 per question; more findings: one question per batch of 4, in Qodo's order). Label each
with severity and `file:line`, put the recommendation in its description ("Recommended: fix", or
"Recommended: dismiss as false positive, because ..."), and pre-select nothing. Example:

```
AskUserQuestion(questions=[{
  question: "Which Qodo findings should I fix?",
  multiSelect: true,
  options: [
    {label: "CRITICAL auth.py:156", description: "SQL injection + missing validation. Recommended: fix"},
    {label: "HIGH service.py:42",   description: "Null dereference on empty cart. Recommended: fix"},
    {label: "MEDIUM utils.py:18",   description: "Performance. Recommended: defer (out of scope)"},
    {label: "LOW helpers.py:5",     description: "Naming. Recommended: dismiss as intentional"}
  ]
}])
```

Selected findings are fixed. Each unselected finding gets the recommendation in its description; one
recommended as fix is declined instead: defer it, record no outcome. For a different outcome, the user
says so in the "Other" answer. Only after the answer, move to Phase 3.

**Defaults when user says "go ahead" or similar:**
- CRITICAL/HIGH: Apply fix
- MEDIUM: Defer
- LOW: Fix (batched)

### Phase 3: EXECUTE

**Step 1: Detect Configuration**
- Auto-detect test/lint/format commands from project config
- See [Test Integration Guide](references/test-integration.md)

**Step 2: Fix → Commit (Per Issue)**

Process each issue individually in Qodo's original order, one commit per fix, so git history stays clean.

For each issue the user approved as "fix":
1. **Apply** the code change, guided by the finding's description, `location` and evidence
   (fallback path: the Agent Prompt)
2. **Verify** all sub-issues addressed (for multi-issue findings)
3. **Commit** with Conventional Commits format: `fix: <issue title>` (see [Commit Strategy Guide](references/commit-strategy.md))
4. **Fallback path only:** reply to every comment location of this issue using [Reply Templates](references/reply-templates.md), then resolve the thread(s) via GitHub GraphQL API

Skip issues the user chose to ignore: no reply, no outcome recorded.

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

**Step 6: Record Outcomes in Qodo (structured path)**

Qodo's write tools update its record, resolve or strike through the PR comments, and re-render the
review summary, so no GitHub replies are needed on this path.
- **Fixed findings:** prefer Qodo's own re-attribution after the re-review (Step 9): it marks a
  finding `implemented` once it sees the fix. Use `mark-implemented` only when the user explicitly
  asks to clear them now, because it clears the merge gate without a review having checked the fix.
- **Not fixed:** `dismiss` with the reason the user approved: `false_positive` (wrong), `intentional`
  (correct as written), `deferred` (real, out of scope), `rejected` (declined). Always add an explanation.
- Show the exact command(s) and get a yes before running them. Batch all findings with the same
  outcome into one call:
  ```bash
  qodo pr-review-session dismiss --finding-ids <id>,<id> --reason deferred \
    --explanation "Tracked in <issue>; out of scope for this PR" --json
  qodo pr-review-session mark-implemented --finding-ids <id>,<id> --json
  ```
- Check the per-finding `results` in the output: an already-closed id comes back with its own outcome
  rather than failing the call. Report any that did not change.

*Fallback path:* deferred and declined issues get a reply with the reason and a resolved thread
(no code change); optionally add a +1 reaction on Qodo's main review comment.

**Step 7: Fresh Verification**
- Re-fetch the findings (structured path) or PR comments (fallback path)
- Confirm zero open findings or unresolved threads beyond the ones the user chose to leave
- Verify all CI checks passing
- Provide completion summary

**Step 8: Show PR URL**
- Print the PR link now, before any polling can stop the skill:
  ```
  PR: {pr_url}
  ```

**Step 9: Trigger Qodo's Re-review**
Qodo reviews a new push only when asked: it does not re-review on its own. After the fixes are pushed and the threads resolved, post the trigger comment:
```bash
gh pr comment {pr_number} --body "/agentic_review"
```
Before posting:
- Read the PR's head SHA from GitHub (`gh pr view {pr_number} --json headRefOid -q .headRefOid`), not local `HEAD`, and check it matches local `HEAD`; if not, the push did not land, so stop and say so.
- If a `/agentic_review` comment already exists after the last push and no Qodo update names that SHA yet, a re-review is already pending: do not post another, just wait.

Some repos review every push on their own: on the structured path, check first whether a run at the new head already started (`review_session.commit_sha` equals the new head) and skip the trigger if so.

Then wait for the new review as in Phase 0. On the structured path the head-SHA rule already excludes the previous review. On the fallback path use one stricter readiness rule: the previous review stays visible, so it must not count. Note the trigger comment's ID and time; the re-review is ready only when a comment by the Qodo bot created after the trigger names the exact head SHA (Qodo posts "Code review by qodo was updated up to the latest commit <sha>") and no placeholder is showing. Put the SHA, the trigger time and this rule in the cron prompt too. On either path, stop waiting after about 20 minutes: delete the cron and report that no re-review arrived, with the trigger comment's link, instead of polling forever. Then run this skill again on any new findings. Skip this step when nothing was pushed.

## Severity Classification

| Severity | Qodo Indicators | Keywords | Priority |
|----------|-----------------|----------|----------|
| **CRITICAL** | ⛨ Security, 🐞 Bug (security) | security, vulnerability, injection, XSS, SQL | Must fix first |
| **HIGH** | 🐞 Bug, ⛯ Reliability | bug, error, crash, fail, memory leak | Should fix |
| **MEDIUM** | 📘 Rule violation, ✓ Correctness | performance, refactor, code smell, rule violation | Recommended |
| **LOW** | 📎 Requirement gaps (minor) | style, nit, formatting, typo | Optional |

**Structured path mapping** (from `category` + `action_level`):

| `action_level` | Severity | Tests required |
|---|---|---|
| `action_required`, security category | CRITICAL | Yes |
| `action_required` | HIGH | Yes |
| `remediation_recommended` | MEDIUM | Recommended |
| `informational` | LOW | Optional |

The sub-agent may raise or lower one step when the code disagrees with Qodo's grade, and says why.

**Processing order**: CRITICAL → HIGH → MEDIUM → LOW

For Qodo badge-to-severity mapping, see [Qodo Parsing Guide](references/qodo-parsing.md). For detailed classification rules, see [Severity Guide](references/severity-guide.md).

## Qodo-Specific Handling

For detailed parsing instructions (API calls, HTML structure, badge detection, deduplication), see the [Qodo Parsing Guide](references/qodo-parsing.md). Read it during Phase 1 Step 2 when fetching and parsing comment data.

**Key points:**
- Qodo posts in **two locations** (general summary + inline comments): fetch both
- Deduplicate by `file:line:title` before launching sub-agents
- Extract Agent Prompt sections as primary fix guidance
- Use Qodo reply format for responses (see [Reply Templates](references/reply-templates.md))

## Quick Examples

**Example 1: Review already ready (structured path)**
```
/qodo-pr-resolver

→ Pre-check: All code pushed ✓, checkout matches PR head ✓
→ Phase 0: qodo CLI 2.1.0, logged in → structured path
→ Phase 0: review_session completed at head a1b2c3d ✓

→ Phase 1: 2 open findings (1 action_required, 1 remediation_recommended)
→ Phase 1: Launching 2 sub-agents in parallel to analyze each finding...
→ Phase 1: All sub-agents complete. Findings annotated with severity.

→ Phase 2: AskUserQuestion (multi-select): "Which Qodo findings should I fix?"
   User: selects HIGH service.py:42; MEDIUM utils.py:18 stays "defer"

→ Phase 3: Fix #1 (HIGH) → commit ✓
→ Phase 3: Running tests ✓
→ Phase 3: Pushing all commits...
→ Phase 3: Approved: qodo pr-review-session dismiss --reason deferred (1 finding) ✓
→ Phase 3: Posted /agentic_review, polling for a review at the new head...
→ Summary: 1 HIGH fixed (awaiting Qodo re-attribution), 1 MEDIUM deferred
→ PR: https://github.com/owner/repo/pull/123
```

**Example 2: Review still generating (polling)**
```
/qodo-pr-resolver

→ Checking Qodo review status... review_session.status = started
→ Setting up polling every 2 minutes...
→ Cron job created. You can keep working; I'll notify you when the review is ready.

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
- **One sub-agent per issue**: Each Qodo issue gets its own Agent(subagent_type="general-purpose") call; never analyze issues inline in the parent process
- **Launch all at once**: Put all Agent tool calls in a single response so they run concurrently
- **Pass full context**: Each sub-agent needs the file path, line range, and the finding ID with its description and evidence (fallback path: raw HTML body and comment IDs)
- **Severity first**: Classify before recommending action
- **Detect multi-issue**: Look for "AND", "also", "additionally"
- **Include CI checks**: Analyze failing checks alongside comments

### Confirmation Phase
- **Always use AskUserQuestion**: Never skip confirmation: this is a hard gate before Phase 3
- **One multi-select question**: findings in Qodo's order, nothing pre-selected, recommendation in each description
- **Smart defaults**: If user says "go ahead" → CRITICAL/HIGH=fix, MEDIUM=defer, LOW=fix(batch)

### Execution Phase
- **One commit per fix**: Apply → commit for each issue before moving to the next
- **Preserve Qodo's order**: Process issues in Qodo's original order, not re-sorted by severity
- **Verify multi-issue**: Confirm ALL sub-issues addressed
- **Test before push**: NEVER push failing tests
- **Use templates**: Consistent professional replies
- **Record outcomes in Qodo**: `dismiss` / `mark-implemented` only after the user approves the exact command
- **Show PR URL**: Print the PR link at the end
- **Fresh verification**: Always re-fetch to confirm completion

## Gotchas

- `qodo` prints a trace line on stderr: run it outside the repo with `2>/dev/null`, or the JSON will not parse.
- `qodo update` never crosses a major version: a 1.x CLI reports "up to date" while the skill needs 2.0+.
- Structured findings carry no GitHub comment IDs: close them through Qodo's tools, not thread replies.
- `mark-implemented` clears the merge gate without a review checking the fix: prefer re-attribution.
- Only a completed review whose `commit_sha` is the PR head counts; an older run describes other code.

## Related skills

**Before:** clean up and commit your work (your own cleanup or commit workflow, if you have one).

**After:**
- Track deferred items in your issue tracker.
- Verify: `gh pr checks` (all CI passing).

See [Advanced Usage](references/advanced-usage.md) for complete workflow examples.

## Memory

State and learnings: follow `~/.claude/memory/AGENTS.md` if present, else `~/.claude/qodo-pr-resolver/`.

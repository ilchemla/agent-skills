# GitHub API Reference

Complete reference for GitHub CLI (`gh`) commands used in this skill.

## Prerequisites

```bash
# Check gh is installed
gh --version

# Authenticate
gh auth login

# Check authentication status
gh auth status
```

## PR Information

### Get Current PR Number

```bash
gh pr view --json number -q .number
```

### Get PR Details

**IMPORTANT**: Use only tested, available fields. The `repository` field does NOT exist in `gh pr view` output.

**Safe Fields** (always available):
- `number`, `title`, `url`, `state`
- `headRefName`, `baseRefName` (branch names)
- `headRepositoryOwner`, `author` (user objects)

```bash
# ✅ CORRECT: Use headRepositoryOwner (not repository)
gh pr view --json number,title,url,headRefName,headRepositoryOwner \
  --jq '{
    owner: .headRepositoryOwner.login,
    repo: "your-repo",
    number: .number,
    title: .title,
    branch: .headRefName,
    url: .url
  }'

# ❌ WRONG: repository field doesn't exist
gh pr view --json repository  # ERROR: Unknown JSON field

# ✅ List all available fields
gh pr view --json-fields
```

## Review Comments

### Two Types of Qodo Comments

**CRITICAL**: Qodo posts comments in **two separate locations**. You must fetch **both** to get all issues.

1. **General Comments** - Summary on PR conversation (via issues API)
2. **Inline Comments** - Specific code line comments (via pulls API)

### Fetch General Comments (Summary)

General comments contain **all issues** in a single comment with multiple nested `<details>` sections.

```bash
# Fetch general PR comments from Qodo
gh api repos/{owner}/{repo}/issues/{pr_number}/comments --jq '[.[] |
  select(.user.login == "qodo-code-review[bot]" or .user.login == "qodo-merge[bot]")
]'

# Example output structure
# {
#   "id": 123456789,
#   "body": "<h3>Code Review by Qodo</h3>\n<details><summary>1. Issue Title...</summary>...",
#   "user": {"login": "qodo-code-review[bot]"}
# }
```

**IMPORTANT**: Direct comment access by ID returns 404. Always use array filtering:
```bash
# ❌ FAILS with 404
gh api repos/{owner}/{repo}/issues/comments/{comment_id}

# ✅ WORKS - use array filtering
gh api repos/{owner}/{repo}/issues/{pr_number}/comments --jq '[.[] | select(.id == {comment_id})][0]'
```

### Fetch Inline Comments

Inline comments are posted on specific code lines.

```bash
# Fetch inline review comments from Qodo
gh api repos/{owner}/{repo}/pulls/{pr_number}/comments --jq '[.[] |
  select(.user.login == "qodo-code-review[bot]" or .user.login == "qodo-merge[bot]") |
  select(.in_reply_to_id == null)
]'

# Example output includes metadata
# {
#   "id": 987654321,
#   "path": "src/services/example.py",
#   "line": 42,
#   "body": "...",
#   "user": {"login": "qodo-code-review[bot]"}
# }
```

### Parse General Comments (Multiple Issues)

General comments contain multiple issues in nested `<details>` blocks:

```bash
# Full general comment body
COMMENT_BODY=$(gh api repos/{owner}/{repo}/issues/{pr_number}/comments --jq '[.[] |
  select(.user.login == "qodo-code-review[bot]")][0].body')

# Structure:
# <h3>Code Review by Qodo</h3>
# <code>🐞 Bugs (0)</code> <code>📘 Rule violations (2)</code>
# <details>
#   <summary>1. Issue Title <code>📘 Rule violation</code></summary>
#   <details><summary>Description</summary>...</details>
#   <details><summary>Code</summary>...</details>
#   <details><summary>Evidence</summary>...</details>
#   <details><summary>Agent prompt</summary>...</details>
# </details>
# <details>
#   <summary>2. Another Issue...</summary>
#   ...
# </details>
```

**Extract all issues from general comment:**
1. Split on outer `<details>` tags to separate issues
2. Each issue has numbered summary: `<summary>1. Title <code>📘 Rule violation</code></summary>`
3. Parse file/line from GitHub links: `[app/file.py[R363-380]](https://github.com/...)`
4. Extract Agent Prompt from nested `<details><summary>Agent prompt</summary>`

### Parse Inline Comments (Single Issue)

Simpler structure with metadata:

```bash
# Extract clean text from HTML comment (use array filtering, not direct ID)
COMMENT_BODY=$(gh api repos/{owner}/{repo}/pulls/{pr_number}/comments --jq '[.[] |
  select(.id == {comment_id})][0].body')

# Metadata available directly
PATH=$(gh api repos/{owner}/{repo}/pulls/{pr_number}/comments --jq '[.[] |
  select(.id == {comment_id})][0].path')
LINE=$(gh api repos/{owner}/{repo}/pulls/{pr_number}/comments --jq '[.[] |
  select(.id == {comment_id})][0].line')

# Extract Agent Prompt section (contains fix instructions)
AGENT_PROMPT=$(echo "$COMMENT_BODY" | grep -A 20 '<summary>Agent Prompt</summary>' | sed 's/<[^>]*>//g')

# Extract severity badges
SEVERITY=$(echo "$COMMENT_BODY" | grep -oE '(🐞 Bug|📘 Rule violation|⛨ Security|✓ Correctness|⛯ Reliability)')

# Extract numbered issue title
ISSUE_TITLE=$(echo "$COMMENT_BODY" | grep -oE '[0-9]+\. [^<]+' | head -1)
```

### Extract Agent Prompt

The Agent Prompt section contains ready-to-use fix instructions:

```bash
# Extract full Agent Prompt content
gh api repos/{owner}/{repo}/pulls/comments/{comment_id} --jq '.body' | \
  sed -n '/<summary>Agent Prompt<\/summary>/,/<\/details>/p' | \
  sed 's/<[^>]*>//g' | \
  sed '/^$/d'
```

**Agent Prompt Structure:**
```
## Issue description
[Description of the problem]

## Issue Context
[Context and background]

## Fix Focus Areas
- file.py[line1-line2]
```

### Get Comment Details

```bash
# Specific comment
gh api repos/{owner}/{repo}/pulls/comments/{comment_id}

# Extract fields
gh api repos/{owner}/{repo}/pulls/comments/{comment_id} \
  --jq '{id, body, path, line, resolved}'
```

## Posting Replies

### Two Reply Endpoints

Different endpoints for general vs inline comments:

**Reply to General Comment (on PR conversation):**
```bash
# Uses issues comment API
gh api repos/{owner}/{repo}/issues/comments/{comment_id}/replies \
  --method POST \
  --input - <<EOF
{
  "body": "Reply text here"
}
EOF
```

**Reply to Inline Comment (on code line):**
```bash
# Uses pull request review comment API
gh api repos/{owner}/{repo}/pulls/comments/{comment_id}/replies \
  --method POST \
  --input - <<EOF
{
  "body": "Reply text here"
}
EOF
```

**IMPORTANT**:
- Use correct endpoint based on comment type
- Use `--input -` (not `-f`) for proper JSON handling
- For issues in both locations, post replies to both

### Post with Variables

```bash
COMMIT_HASH=$(git rev-parse --short HEAD)

# Reply to inline comment
gh api repos/{owner}/{repo}/pulls/comments/{inline_comment_id}/replies \
  --method POST \
  --input - <<EOF
{
  "body": "Fixed in ${COMMIT_HASH}: Description here"
}
EOF

# Also reply to same issue in general comment
gh api repos/{owner}/{repo}/issues/comments/{general_comment_id}/replies \
  --method POST \
  --input - <<EOF
{
  "body": "Fixed in ${COMMIT_HASH}: Description here"
}
EOF
```

### Multi-line Reply

```bash
gh api repos/{owner}/{repo}/pulls/comments/{comment_id}/replies \
  --input - <<EOF
{
  "body": "Fixed in abc123f: Prevent SQL injection\n\nAll issues addressed:\n- ✅ SQL injection eliminated\n- ✅ Input validation added"
}
EOF
```

## Thread Resolution

### Resolve Thread via GraphQL

```bash
# Get thread ID first
THREAD_ID=$(gh api repos/{owner}/{repo}/pulls/comments/{comment_id} --jq '.pull_request_review_id')

# Resolve the thread
gh api graphql -f query='
  mutation {
    resolveReviewThread(input: {threadId: "'"${THREAD_ID}"'"}) {
      thread {
        isResolved
      }
    }
  }'
```

### Check Thread Status

```bash
gh api repos/{owner}/{repo}/pulls/comments/{comment_id} \
  --jq '.in_reply_to_id, .resolved'
```

## CI Checks

### Get Check Status

**IMPORTANT**: Avoid `!=` in jq (shell escaping issues). Use positive matching or `.state` field instead.

```bash
# All checks
gh pr checks

# JSON format (use 'state' not 'conclusion')
gh pr checks --json name,state

# ✅ CORRECT: Failing checks (positive matching)
gh pr checks --json name,state \
  --jq '[.[] | select(.state == "FAILURE" or .state == "ERROR")]'

# ❌ WRONG: != gets escaped as \!=
gh pr checks --jq 'select(.state != "SUCCESS")'  # Shell escaping breaks jq
```

### Count Failing Checks

```bash
# Count failures and errors
gh pr checks --json state \
  --jq '[.[] | select(.state == "FAILURE" or .state == "ERROR")] | length'
```

## Verification

### Count Unresolved Comments

```bash
gh api repos/{owner}/{repo}/pulls/{pr_number}/comments \
  --jq '[.[] | select(.user.login | contains("qodo") or contains("pr-agent")) | select(.resolved == false)] | length'
```

### Fresh Data Fetch

```bash
# Re-fetch after execution
UNRESOLVED_COUNT=$(gh api repos/{owner}/{repo}/pulls/${PR_NUM}/comments \
  --jq '[.[] | select(.user.login | contains("qodo") or contains("pr-agent")) | select(.resolved == false)] | length')

echo "Unresolved comments remaining: ${UNRESOLVED_COUNT}"
```

## Common Patterns

### Get Owner and Repo

```bash
OWNER=$(gh pr view --json repository -q '.repository.owner.login')
REPO=$(gh pr view --json repository -q '.repository.name')
PR_NUM=$(gh pr view --json number -q '.number')

echo "PR: ${OWNER}/${REPO}#${PR_NUM}"
```

### Iterate Over Comments

```bash
gh api repos/{owner}/{repo}/pulls/{pr_number}/comments \
  --jq '.[] | select(.resolved == false) | .id' | \
while read comment_id; do
  echo "Processing comment ${comment_id}"
  # Process each comment
done
```

### Error Handling

```bash
# Check if PR exists
if ! gh pr view --json number &>/dev/null; then
  echo "Error: Not in a PR branch"
  exit 1
fi

# Retry on API failure
MAX_RETRIES=3
for i in $(seq 1 $MAX_RETRIES); do
  if gh api repos/{owner}/{repo}/pulls/{pr_number}/comments; then
    break
  fi
  echo "Retry $i/$MAX_RETRIES..."
  sleep 2
done
```

## Response Formats

### Comment Object

```json
{
  "id": 123456789,
  "pull_request_review_id": 987654321,
  "user": {
    "login": "qodo-merge-pro[bot]"
  },
  "body": "Consider adding error handling",
  "path": "src/auth.py",
  "line": 42,
  "commit_id": "abc123...",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "in_reply_to_id": null,
  "resolved": false
}
```

### CI Check Object

```json
{
  "name": "ESLint",
  "conclusion": "failure",
  "detailsUrl": "https://github.com/..."
}
```

## Rate Limiting

Check rate limit status:

```bash
gh api rate_limit --jq '.resources.core'
```

## Troubleshooting

### Authentication Issues

```bash
# Re-authenticate
gh auth logout
gh auth login

# Use different account
gh auth login --hostname github.com
```

### API Errors

```bash
# Verbose output for debugging
gh api repos/{owner}/{repo}/pulls/{pr_number}/comments --verbose

# Check response headers
gh api repos/{owner}/{repo}/pulls/{pr_number}/comments --include
```

### GraphQL Errors

```bash
# Test GraphQL query
gh api graphql -f query='
  query {
    viewer {
      login
    }
  }
' --jq '.data.viewer.login'
```

## Error Handling & Best Practices

### Common Errors and Solutions

#### 1. Unknown JSON Field Errors

**Error:**
```
Unknown JSON field: "repository"
```

**Cause:** Using field names that don't exist in the API response

**Solution:**
```bash
# ❌ WRONG: Assuming field exists
gh pr view --json repository

# ✅ CORRECT: Check available fields first
gh pr view --json-fields

# ✅ CORRECT: Use only tested fields
gh pr view --json number,title,headRepositoryOwner
```

**Safe Fields Reference:**
- PR: `number`, `title`, `url`, `state`, `headRefName`, `baseRefName`, `headRepositoryOwner`, `author`
- Checks: `name`, `state` (not `conclusion`)
- Comments: `id`, `body`, `path`, `line`, `user`, `created_at`

#### 2. Parallel Command Failures

**Error:**
```
Error: Sibling tool call errored
```

**Cause:** When running parallel Bash commands, if ONE fails, ALL siblings abort

**Solution:**
```bash
# ❌ BAD: Mix risky and safe commands in parallel
gh pr view --json badfield &  # This fails
gh api repos/owner/repo/pulls/101/comments &  # Gets aborted
wait

# ✅ GOOD: Validate first, then parallelize
# Step 1: Validate critical data (sequential)
PR_NUM=$(gh pr view --json number -q .number) || exit 1
OWNER="your-org"
REPO="your-repo"

# Step 2: Fetch data (parallel - now safe)
gh api repos/$OWNER/$REPO/issues/$PR_NUM/comments &
gh api repos/$OWNER/$REPO/pulls/$PR_NUM/comments &
wait
```

**Best Practice:** Group commands by risk level
- **Phase 1:** Validate (sequential, may fail)
- **Phase 2:** Fetch (parallel, unlikely to fail)
- **Phase 3:** Process (sequential or parallel as needed)

#### 3. Shell Escaping in jq

**Error:**
```
unexpected token "\\"
```

**Cause:** Shell escapes special characters like `!=` as `\!=`, breaking jq syntax

**Solution:**
```bash
# ❌ WRONG: != operator
jq 'select(.state != "SUCCESS")'  # Becomes select(.state \!= "SUCCESS")

# ✅ CORRECT: Positive matching
jq 'select(.state == "FAILURE" or .state == "ERROR")'

# ✅ CORRECT: Regex matching
jq 'select(.state | test("FAIL|ERROR"))'

# ✅ CORRECT: Array membership
jq 'select([.state] | inside(["FAILURE", "ERROR"]))'
```

**Problematic Characters:**
- `!=` → Use `==` with `or` instead
- `!` → Use positive logic
- `>`, `<` → Quote carefully or use functions

#### 4. API 404 Errors with Direct Comment Access

**Error:**
```
{"message": "Not Found", "status": "404"}
```

**Cause:** GitHub API doesn't support direct comment ID access for some endpoints

**Solution:**
```bash
# ❌ WRONG: Direct comment access
gh api repos/owner/repo/issues/comments/123456

# ✅ CORRECT: Use array filtering
gh api repos/owner/repo/issues/101/comments \
  --jq '[.[] | select(.id == 123456)][0]'
```

**Rule:** Always fetch comment arrays and filter, never access by ID directly

### Defensive Programming Patterns

#### Pattern 1: Validate Before Processing

```bash
# Validate repository access
gh api repos/$OWNER/$REPO --jq '.full_name' || {
  echo "Error: Cannot access repository"
  exit 1
}

# Validate PR exists
gh pr view $PR_NUM --json number || {
  echo "Error: PR not found"
  exit 1
}

# Now safe to proceed with main workflow
```

#### Pattern 2: Use Fallbacks

```bash
# Try preferred method, fallback to alternative
OWNER=$(gh pr view --json headRepositoryOwner -q '.headRepositoryOwner.login' 2>/dev/null) || \
  OWNER=$(gh repo view --json owner -q '.owner.login')
```

#### Pattern 3: Fail Fast

```bash
# Exit immediately on errors
set -e

# Or check each critical command
gh api repos/$OWNER/$REPO/pulls/$PR_NUM || exit 1
```

#### Pattern 4: Explicit Field Lists

```bash
# ❌ AVOID: Fetching all fields
gh pr view --json

# ✅ PREFER: Explicit minimal field list
gh pr view --json number,title,url
```

### Testing Commands Before Use

```bash
# Test new gh command before adding to skill
gh pr view --json-fields | grep -i "field_name"

# Test jq expression
echo '{"state": "FAILURE"}' | jq 'select(.state == "FAILURE")'

# Test API endpoint
gh api repos/owner/repo/endpoint --jq '.'
```

### Summary: Error Prevention Checklist

Before adding a command to the skill:

- [ ] Verify all JSON field names exist (`--json-fields`)
- [ ] Avoid `!=` in jq expressions (use positive matching)
- [ ] Don't mix risky/safe commands in parallel
- [ ] Use array filtering instead of direct ID access
- [ ] Test commands manually first
- [ ] Add validation steps before parallel execution
- [ ] Use explicit minimal field lists
- [ ] Add fallbacks for critical operations

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

```bash
# Full PR details
gh pr view --json repository,number,title,body

# Extract specific fields
gh pr view --json repository,number -q '{owner: .repository.owner.login, repo: .repository.name, number: .number}'
```

## Review Comments

### Fetch All Comments

```bash
# All review comments
gh api repos/{owner}/{repo}/pulls/{pr_number}/comments

# With jq filtering
gh api repos/{owner}/{repo}/pulls/{pr_number}/comments | jq '.'
```

### Fetch Unresolved Comments

```bash
gh api repos/{owner}/{repo}/pulls/{pr_number}/comments \
  --jq '[.[] | select(.resolved == false)]'
```

### Fetch Qodo Comments Only

**Important**: Qodo uses the bot username `qodo-code-review[bot]` (exact match required).

```bash
# Fetch Qodo comments (exact username match)
gh api repos/{owner}/{repo}/pulls/{pr_number}/comments | jq '[.[] |
  select(.user.login == "qodo-code-review[bot]") |
  select(
    (.in_reply_to_id == null) or
    (.resolved == false)
  )
]'
```

### Parse Qodo HTML Comments

Qodo comments contain HTML. Extract key information:

```bash
# Extract clean text from HTML comment
COMMENT_BODY=$(gh api repos/{owner}/{repo}/pulls/comments/{comment_id} --jq '.body')

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

### Post Reply to Comment

**IMPORTANT**: Use `--input -` (not `-f`) for proper JSON handling.

```bash
gh api repos/{owner}/{repo}/pulls/comments/{comment_id}/replies \
  --input - <<EOF
{
  "body": "Reply text here"
}
EOF
```

### Post with Variables

```bash
COMMIT_HASH=$(git rev-parse --short HEAD)
gh api repos/{owner}/{repo}/pulls/comments/{comment_id}/replies \
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

```bash
# All checks
gh pr checks

# JSON format
gh pr checks --json name,conclusion,detailsUrl

# Failing checks only
gh pr checks --json name,conclusion \
  --jq '.[] | select(.conclusion != "success")'
```

### Count Failing Checks

```bash
gh pr checks --json conclusion \
  --jq '[.[] | select(.conclusion != "success")] | length'
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

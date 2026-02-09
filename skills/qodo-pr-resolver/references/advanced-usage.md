# Advanced Usage

## Custom Filtering

### Filter by Severity

Process only specific severity levels:

```bash
# Only CRITICAL/HIGH
gh api repos/{owner}/{repo}/pulls/{pr_number}/comments | jq '[.[] |
  select(.body | test("security|vulnerability|injection|bug|error|crash"; "i"))
]'

# Only security-related (CRITICAL)
gh api repos/{owner}/{repo}/pulls/{pr_number}/comments | jq '[.[] |
  select(.body | test("security|vulnerability|injection|XSS|SQL"; "i"))
]'
```

### Filter by File Path

Process comments on specific files or directories:

```bash
# Only comments on src/ directory
gh api repos/{owner}/{repo}/pulls/{pr_number}/comments | jq '[.[] |
  select(.path | contains("src/"))
]'

# Exclude test files
gh api repos/{owner}/{repo}/pulls/{pr_number}/comments | jq '[.[] |
  select(.path | contains("test") | not)
]'

# Specific file type
gh api repos/{owner}/{repo}/pulls/{pr_number}/comments | jq '[.[] |
  select(.path | endswith(".py"))
]'
```

### Filter by Keywords

```bash
# Only performance-related comments
gh api repos/{owner}/{repo}/pulls/{pr_number}/comments | jq '[.[] |
  select(.body | test("performance|optimize|slow|bottleneck"; "i"))
]'

# Exclude nits/style
gh api repos/{owner}/{repo}/pulls/{pr_number}/comments | jq '[.[] |
  select(.body | test("nit|style|formatting"; "i") | not)
]'
```

### Multi-Issue Comments Only

```bash
# Find comments with "AND" or "also"
gh api repos/{owner}/{repo}/pulls/{pr_number}/comments | jq '[.[] |
  select(.body | test(" and | also | additionally | plus "; "i"))
]'
```

## Batch Processing

### Process by Severity Groups

When there are many comments, process in stages:

**Stage 1: CRITICAL/HIGH only**
- Focus on security and bugs first
- Apply fixes and push
- Get these reviewed ASAP

**Stage 2: MEDIUM**
- Address code quality issues
- Can batch these into single commit
- Less urgent than Stage 1

**Stage 3: LOW**
- Address style/formatting
- Batch all into one commit
- Least priority

### Process by File

Group comments by affected file:

```bash
# Get unique files with comments
gh api repos/{owner}/{repo}/pulls/{pr_number}/comments \
  --jq '[.[].path] | unique | .[]'

# Process one file at a time
for file in $(list_of_files); do
  process_comments_for_file "$file"
done
```

### Incremental Processing

For very large PRs (>20 comments):

```bash
# Process first 10 comments
gh api repos/{owner}/{repo}/pulls/{pr_number}/comments \
  --jq '.[:10]'

# After completion, process next 10
gh api repos/{owner}/{repo}/pulls/{pr_number}/comments \
  --jq '.[10:20]'
```

## Integration with Other Skills

### Before Running qodo-review

**1. Clean up code first:**
```bash
/cleanup
```

**2. Ensure tests pass:**
```bash
npm test  # or appropriate test command
```

**3. Commit current work:**
```bash
/commit
```

### After Running qodo-review

**1. Create tickets for deferred items:**
```bash
/create-ticket
# Title: "Address deferred review comment #123"
# Description: Copy from review comment
```

**2. Verify CI status:**
```bash
gh pr checks
```

**3. Request re-review:**
```bash
gh pr review --approve  # If self-review allowed
# Or request reviewer to re-review
```

### Complete Workflow Example

```bash
# 1. Clean up code
/cleanup

# 2. Commit cleanup changes
/commit

# 3. Handle review comments
/qodo-review

# 4. Create tickets for deferred work
/create-ticket

# 5. Verify everything passes
gh pr checks

# 6. Request re-review
gh pr ready  # Mark draft as ready
```

## Custom Test Commands

### Specify Test Commands

If auto-detection fails, set manually:

```bash
# Set environment variables
export TEST_CMD="npm run test:ci"
export LINT_CMD="npm run lint:fix"
export FORMAT_CMD="npm run format"

# Then run skill
/qodo-review
```

### Skip Tests for LOW Severity

When processing only style fixes:

```bash
# Set flag to skip tests
export SKIP_TESTS_FOR_LOW=true

# Process only LOW severity
# Tests will be skipped
```

### Custom Test Timeout

For slow test suites:

```bash
# Set timeout (seconds)
export TEST_TIMEOUT=600  # 10 minutes

# Run with timeout
timeout $TEST_TIMEOUT npm test
```

## Handling Large PRs

### Strategy for 30+ Comments

**Option 1: Multiple Sessions**
1. Run skill for CRITICAL/HIGH
2. Push and get feedback
3. Run skill again for MEDIUM/LOW

**Option 2: Process by Module**
1. Group comments by module/file
2. Process one module at a time
3. More organized, easier to review

**Option 3: Delegate to Issues**
1. Process only CRITICAL immediately
2. Defer everything else to issues
3. Address in future PRs

### Progress Tracking

```bash
# Before starting
TOTAL_COMMENTS=$(gh api repos/{owner}/{repo}/pulls/{pr_number}/comments \
  --jq '[.[] | select(.resolved == false)] | length')

echo "Total unresolved: $TOTAL_COMMENTS"

# After each batch
REMAINING=$(gh api repos/{owner}/{repo}/pulls/{pr_number}/comments \
  --jq '[.[] | select(.resolved == false)] | length')

echo "Progress: $((TOTAL_COMMENTS - REMAINING))/$TOTAL_COMMENTS completed"
```

## Advanced GitHub API Usage

### Pagination for Large Comment Counts

```bash
# Fetch with pagination
PAGE=1
while true; do
  COMMENTS=$(gh api "repos/{owner}/{repo}/pulls/{pr_number}/comments?page=$PAGE&per_page=100")

  if [ "$(echo "$COMMENTS" | jq 'length')" -eq 0 ]; then
    break
  fi

  # Process this page
  process_comments "$COMMENTS"

  PAGE=$((PAGE + 1))
done
```

### Bulk Thread Resolution

```bash
# Resolve multiple threads at once
THREAD_IDS=("id1" "id2" "id3")

for thread_id in "${THREAD_IDS[@]}"; do
  gh api graphql -f query='
    mutation {
      resolveReviewThread(input: {threadId: "'"${thread_id}"'"}) {
        thread { isResolved }
      }
    }
  ' &
done

wait  # Wait for all to complete
```

### Comment Search

```bash
# Find comments by specific reviewer
gh api repos/{owner}/{repo}/pulls/{pr_number}/comments \
  --jq '.[] | select(.user.login == "specific-reviewer")'

# Find comments with reactions
gh api repos/{owner}/{repo}/pulls/{pr_number}/comments \
  --jq '.[] | select(.reactions.total_count > 0)'
```

## Custom Severity Keywords

### Add Project-Specific Keywords

Create custom severity classification:

```bash
# Custom CRITICAL keywords for your project
CRITICAL_KEYWORDS="security|vulnerability|auth|payment|data-loss"

# Custom HIGH keywords
HIGH_KEYWORDS="bug|crash|error|memory-leak|deadlock"

# Apply custom classification
gh api repos/{owner}/{repo}/pulls/{pr_number}/comments | jq --arg crit "$CRITICAL_KEYWORDS" --arg high "$HIGH_KEYWORDS" '[.[] |
  if .body | test($crit; "i") then .severity = "CRITICAL"
  elif .body | test($high; "i") then .severity = "HIGH"
  else .severity = "MEDIUM"
  end
]'
```

## Commit Customization

### Custom Commit Message Format

Adjust commit format for your team:

```bash
# Jira ticket integration
git commit -m "$(cat <<EOF
fix(security): prevent SQL injection [PROJ-123]

Addresses PR comment #456 from qodo-pr-agent

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"

# Add additional trailers
git commit -m "$(cat <<EOF
fix: add null check

Addresses PR comment #456

Reviewed-By: @teammate
Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"
```

### Squash After Completion

If you want cleaner history:

```bash
# After all fixes applied
git rebase -i HEAD~5  # Squash last 5 commits

# Or use GitHub's squash merge when merging PR
```

## Monitoring and Reporting

### Generate Report

```bash
# Create summary report
cat > review_report.md <<EOF
# PR Review Summary

## Comments Processed
- Total: $TOTAL_COMMENTS
- CRITICAL: $CRITICAL_COUNT
- HIGH: $HIGH_COUNT
- MEDIUM: $MEDIUM_COUNT
- LOW: $LOW_COUNT

## Actions Taken
- Fixes applied: $FIXES_APPLIED
- Replies posted: $REPLIES_POSTED
- Deferred: $DEFERRED_COUNT

## Test Results
- Tests passing: $TESTS_PASSING
- CI checks passing: $CI_PASSING

## Time Taken
- Started: $START_TIME
- Completed: $END_TIME
- Duration: $DURATION
EOF
```

### Metrics Collection

```bash
# Track metrics
echo "$(date),PR#$PR_NUM,$TOTAL_COMMENTS,$FIXES_APPLIED,$DURATION" >> metrics.csv
```

## Tips for Power Users

1. **Use shell aliases:**
   ```bash
   alias qr='/qodo-review'
   alias qr-crit='qodo-review --severity=critical'
   ```

2. **Create templates:**
   - Save common reply templates
   - Reuse for similar comments

3. **Automate with hooks:**
   - Run after Qodo review webhook
   - Auto-process LOW severity

4. **Monitor PR health:**
   - Track comment resolution rate
   - Identify common issues
   - Improve code quality over time

# Troubleshooting Guide

## Common Issues and Solutions

### No Comments Found

**Symptoms:**
- Skill reports "0 unresolved comments"
- Expected to see Qodo comments but none appear

**Solutions:**

1. **Check PR has been reviewed:**
   ```bash
   gh pr view --json reviews
   ```

2. **Verify PR number:**
   ```bash
   gh pr view --json number -q .number
   ```

3. **Check if comments were resolved:**
   ```bash
   gh api repos/{owner}/{repo}/pulls/{pr_number}/comments \
     --jq '.[] | {id, body, resolved}'
   ```

4. **Verify bot username:**
   ```bash
   # Check actual bot username in comments
   gh api repos/{owner}/{repo}/pulls/{pr_number}/comments \
     --jq '.[].user.login' | sort -u
   ```

   If bot uses different name, update filter accordingly.

### Cannot Post Reply

**Symptoms:**
- Error when trying to post comment reply
- "404 Not Found" or "403 Forbidden"

**Solutions:**

1. **Check authentication:**
   ```bash
   gh auth status

   # Re-authenticate if needed
   gh auth logout
   gh auth login
   ```

2. **Verify write access:**
   ```bash
   gh api repos/{owner}/{repo} --jq '.permissions'
   ```

3. **Confirm PR is still open:**
   ```bash
   gh pr view --json state -q .state
   ```

4. **Use correct JSON format:**
   ```bash
   # ✅ Correct
   gh api ... --input - <<EOF
   {"body": "text"}
   EOF

   # ❌ Wrong
   gh api ... -f body="text"
   ```

### Tests Failing After Fixes

**Symptoms:**
- Tests pass before changes
- Tests fail after applying fixes
- Unclear which test is affected

**Solutions:**

1. **Review test output carefully:**
   ```bash
   npm test 2>&1 | tee test_output.log
   # Review test_output.log for details
   ```

2. **Check if test relies on old behavior:**
   - Read the failing test code
   - Determine if test needs updating
   - Ask user if test expectation should change

3. **Run specific test:**
   ```bash
   # Node.js
   npm test -- --grep "specific test name"

   # Python
   pytest tests/test_specific.py::test_function
   ```

4. **Rollback and analyze:**
   ```bash
   git stash
   npm test  # Should pass
   git stash pop
   npm test  # Should fail - now compare
   ```

### Cannot Resolve Threads

**Symptoms:**
- Thread resolution API call fails
- Error: "Resource not accessible by integration"

**Solutions:**

1. **Verify thread ID is correct:**
   ```bash
   gh api repos/{owner}/{repo}/pulls/comments/{comment_id} \
     --jq '.pull_request_review_id'
   ```

2. **Check GraphQL API access:**
   ```bash
   gh api graphql -f query='query { viewer { login } }'
   ```

3. **Use alternative resolution method:**
   - Threads can be marked as resolved manually in GitHub UI
   - Not critical if API fails - warn and continue

4. **Check permissions:**
   - May need "write" access to resolve threads
   - Some organizations restrict GraphQL access

### Severity Classification Unclear

**Symptoms:**
- Unclear which severity level to assign
- Comment doesn't match obvious patterns

**Solutions:**

1. **Default to MEDIUM if ambiguous:**
   - Between HIGH and MEDIUM → Choose MEDIUM
   - Between MEDIUM and LOW → Choose MEDIUM

2. **Ask user for clarification:**
   - Present the comment to user
   - Offer severity options
   - Let user decide

3. **Consider context:**
   - Security-related code → Higher severity
   - Test files → Lower severity
   - Public APIs → Higher severity

4. **When in doubt, use keywords:**
   - Contains "security" → CRITICAL
   - Contains "bug" or "error" → HIGH
   - Contains "performance" → MEDIUM
   - Contains "style" → LOW

### Multi-Issue Comment Incomplete

**Symptoms:**
- Fixed one issue but comment has multiple
- Forgot to address all sub-issues

**Solutions:**

1. **Re-read comment carefully:**
   - Look for "and", "also", "additionally"
   - Count distinct issues mentioned
   - List each sub-issue explicitly

2. **Check fix addresses all:**
   ```markdown
   Comment: "Fix null check AND add logging AND update tests"

   Fix checklist:
   - [x] Null check added
   - [x] Logging added
   - [ ] Tests updated  ← MISSING!
   ```

3. **Update fix to include all:**
   - Apply additional changes
   - Verify each sub-issue in fix proposal
   - List completion status in reply

4. **Mark in commit message:**
   ```
   All sub-issues addressed:
   - ✅ Null check
   - ✅ Logging
   - ✅ Tests
   ```

### Test Command Not Found

**Symptoms:**
- Auto-detection fails
- No test command found in project config

**Solutions:**

1. **Manual inspection:**
   ```bash
   cat package.json | jq '.scripts'
   cat pyproject.toml | grep -A5 "\[tool"
   cat Makefile | grep "^test"
   ```

2. **Ask user for test command:**
   - Use AskUserQuestion
   - Let user specify command
   - Store for this session

3. **Check language-specific locations:**
   - Node.js: `package.json`, `npm test`
   - Python: `pyproject.toml`, `tox.ini`, `pytest`
   - Go: `go.mod`, `go test ./...`
   - Rust: `Cargo.toml`, `cargo test`

4. **Skip tests for LOW severity:**
   - If only style fixes, can skip tests
   - Warn user tests weren't run
   - Not recommended for CRITICAL/HIGH

### CI Checks Still Failing

**Symptoms:**
- Fixed lint/format issues
- CI checks still show as failing
- GitHub UI shows red X

**Solutions:**

1. **Re-fetch CI status:**
   ```bash
   gh pr checks --json name,conclusion
   ```

2. **Check if CI is running:**
   - May take time to complete
   - Wait for CI to finish
   - Re-check after a few minutes

3. **Review CI logs:**
   ```bash
   gh pr checks --json detailsUrl -q '.[].detailsUrl'
   # Open URL to see detailed logs
   ```

4. **Fix additional issues:**
   - CI may have found new issues
   - Apply additional fixes
   - Push and wait for CI again

### Fresh Verification Shows Unresolved Items

**Symptoms:**
- Completed all fixes
- Verification shows unresolved comments
- Expected 0 but got >0

**Solutions:**

1. **Check if new comments added:**
   ```bash
   gh api repos/{owner}/{repo}/pulls/{pr_number}/comments \
     --jq '.[] | {id, body, created_at, resolved}'
   ```

2. **Verify thread resolution succeeded:**
   - Check if resolution API calls completed
   - May need to retry resolution
   - Can resolve manually in GitHub UI

3. **Confirm GitHub API is fresh:**
   ```bash
   # Force fresh fetch with timestamp
   gh api repos/{owner}/{repo}/pulls/{pr_number}/comments?t=$(date +%s)
   ```

4. **Re-run skill for remaining:**
   - If new comments appeared, re-run
   - Process additional comments
   - Verify again

### Analysis Takes Too Long

**Symptoms:**
- Analysis phase not completing
- Many comments to process
- Sub-agents running indefinitely

**Solutions:**

1. **Process by severity group:**
   - First run: CRITICAL/HIGH only
   - Second run: MEDIUM/LOW
   - Reduces parallel agent load

2. **Check for stuck agents:**
   - Review agent output
   - May be waiting for large file reads
   - Consider timeout

3. **Batch similar comments:**
   - Group by file
   - Group by type
   - Reduces total analysis needed

4. **Monitor progress:**
   - Show progress indicator
   - Log each completed analysis
   - Estimate remaining time

## Error Messages

### "Not in a PR branch"

**Cause:** Current branch doesn't have an associated PR

**Solution:**
```bash
# Check current branch
git branch --show-current

# Create PR if needed
gh pr create
```

### "Resource not accessible by integration"

**Cause:** Insufficient permissions for GraphQL API

**Solution:**
- Check token scopes in `gh auth status`
- Re-authenticate with correct scopes
- May need admin to grant access

### "API rate limit exceeded"

**Cause:** Too many API requests

**Solution:**
```bash
# Check rate limit
gh api rate_limit

# Wait and retry
sleep 60
```

### "Invalid JSON"

**Cause:** Malformed JSON in API request

**Solution:**
- Use `--input -` instead of `-f`
- Validate JSON with `jq`
- Check for unescaped quotes

## Getting Help

If issue persists:

1. **Check GitHub CLI docs:**
   ```bash
   gh pr --help
   gh api --help
   ```

2. **Review GitHub API logs:**
   ```bash
   gh api ... --verbose
   ```

3. **Test manually:**
   - Try operations in GitHub UI
   - Verify expected behavior
   - Compare with CLI results

4. **Report issue:**
   - Include error messages
   - Show commands run
   - Provide repo/PR details (if public)

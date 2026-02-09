# Commit Strategy

## Overview

Use strategic commit organization based on severity and type of changes.

## Strategy by Severity

| Severity | Strategy | Reason |
|----------|----------|--------|
| CRITICAL/HIGH | Individual commits | Each fix is important, needs clear history |
| MEDIUM/LOW | Batch commits | Group related cosmetic changes |
| CI Fixes | Separate commit | Keep CI fixes distinct from feature changes |

## Conventional Commits Format

All commits follow [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Commit Types by Severity

**CRITICAL:**
```
fix(security): prevent SQL injection in user query
fix(critical): add authentication check for admin endpoints
```

**HIGH:**
```
fix: add null check to prevent crash
fix(bug): correct race condition in connection pool
```

**MEDIUM:**
```
refactor: improve code organization in auth module
perf: optimize database query performance
```

**LOW:**
```
style: improve code formatting and naming
docs: update docstrings for clarity
```

**CI Fixes:**
```
ci: fix lint errors in src/app.js
ci: resolve type checking issues
```

## Commit Message Structure

### Subject Line (Required)

- **50 characters max** (hard limit: 72)
- **Imperative mood**: "fix bug" not "fixed bug" or "fixes bug"
- **No period** at the end
- **Lowercase** after the colon

```
✅ fix(auth): prevent unauthorized access
❌ Fix(Auth): Prevented unauthorized access.
```

### Body (Recommended for fixes)

- **Wrap at 72 characters**
- **Explain WHAT and WHY**, not HOW
- **Reference PR comment**

```
fix(security): prevent SQL injection in user query

Addresses PR comment #123 from qodo-pr-agent
- Use parameterized queries instead of string concatenation
- Add input validation before database operations

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

### Footer (Optional)

- **Breaking changes**: `BREAKING CHANGE: description`
- **Issue references**: `Closes #123`
- **PR references**: `Addresses PR comment #456`

## Examples

### Individual Commit (CRITICAL)

```bash
git add auth/middleware.py auth/validators.py
git commit -m "$(cat <<'EOF'
fix(security): prevent SQL injection in user authentication

Addresses PR comment #123 from qodo-pr-agent

Changes:
- Replaced string concatenation with parameterized queries
- Added input validation using SQLAlchemy's text() function
- Implemented prepared statements for all user queries

This prevents attackers from injecting malicious SQL through
username/password fields.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"
```

### Individual Commit (HIGH)

```bash
git add services/data_processor.py
git commit -m "$(cat <<'EOF'
fix: add null check to prevent crash in data processor

Addresses PR comment #124 from qodo-pr-agent

Added null safety check before accessing data.items() to prevent
NullPointerException when data is empty or None.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"
```

### Batched Commit (MEDIUM/LOW)

```bash
git add models/user.py utils/helpers.py views/dashboard.py
git commit -m "$(cat <<'EOF'
style: improve code quality per review feedback

Addresses PR comments #125, #126, #127 from qodo-pr-agent

Changes:
- Rename 'tmp' to 'temporary_user_data' for clarity
- Add docstrings to public methods
- Improve formatting in dashboard view
- Update variable names to follow naming conventions

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"
```

### CI Fix Commit

```bash
git add src/app.js src/utils.js
git commit -m "$(cat <<'EOF'
ci: fix ESLint errors and formatting issues

Resolved:
- 3 ESLint errors in src/app.js (no-unused-vars, prefer-const)
- Formatting issues flagged by Prettier
- Import order violations

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"
```

## Multi-Issue Commits

When a single comment has multiple issues, address all in one commit:

```bash
git commit -m "$(cat <<'EOF'
fix(security): address all authentication vulnerabilities

Addresses PR comment #123 from qodo-pr-agent (multi-issue)

All sub-issues resolved:
1. SQL injection: Implemented parameterized queries
2. Input validation: Added sanitization for all user inputs
3. Rate limiting: Added brute-force protection
4. Error logging: Enhanced security event tracking

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"
```

## Best Practices

### Reference PR Comments

Always reference the source PR comment:

```
Addresses PR comment #123 from qodo-pr-agent
```

For multiple comments in batch commits:

```
Addresses PR comments #124, #125, #126 from qodo-pr-agent
```

### Co-Author Attribution

Always include co-author footer:

```
Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

### Atomic Commits

Each commit should be:
- **Atomic**: Single logical change
- **Complete**: Doesn't break the build
- **Tested**: Tests pass after commit
- **Documented**: Clear message explaining change

### Commit Order

Make commits in this order:

1. CRITICAL fixes (one by one)
2. HIGH fixes (one by one)
3. MEDIUM fixes (batched if related)
4. LOW fixes (batched)
5. CI fixes (separate commit)

### Testing Between Commits

Run tests after each commit to ensure nothing breaks:

```bash
# After each commit
npm test  # or appropriate test command

# If tests fail, amend or rollback
git commit --amend  # Fix and amend
git reset HEAD~1    # Or rollback
```

## Common Scopes

Choose appropriate scope for context:

| Scope | Usage |
|-------|-------|
| `security` | Security-related changes |
| `auth` | Authentication/authorization |
| `api` | API endpoints |
| `db` | Database changes |
| `ui` | User interface |
| `deps` | Dependency updates |
| `config` | Configuration changes |

## Verification

After committing, verify with:

```bash
# View commit log
git log --oneline -n 5

# View specific commit
git show HEAD

# Check commit message format
git log -1 --pretty=format:"%s"
```

## Tools

### Using heredoc for commit messages

Always use heredoc for proper formatting:

```bash
git commit -m "$(cat <<'EOF'
Multi-line
commit message
here
EOF
)"
```

**Never** use multiple `-m` flags - they create separate paragraphs.

### Amending commits

If you need to fix a commit message:

```bash
git commit --amend -m "$(cat <<'EOF'
Corrected commit message
EOF
)"
```

**IMPORTANT**: Only amend if you haven't pushed yet!

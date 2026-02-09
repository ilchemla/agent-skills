# Standard Reply Templates

Use these templates consistently for professional communication with reviewers.

## Qodo-Specific Format

When responding to Qodo comments, match the user's established pattern:

| Action | Qodo Format | Standard Format |
|--------|-------------|----------------|
| **Fixed** | `✅ **FIXED** in commit [hash]` | `Fixed in [hash]: [description]` |
| **Not Applicable** | `❌ **NOT APPLICABLE**` - Reasoning | `Won't fix: [reason]` |
| **Deferred** | `📋 **DEFERRED** to #[issue]` | `Deferred to #[issue]: Will address later` |
| **By Design** | `✅ **BY DESIGN**` - Explanation | `By design: [explanation]` |

**Use Qodo format for Qodo comments, standard format for other reviewers.**

## Template Selection Guide

| Action | Template | When to Use |
|--------|----------|-------------|
| **Fixed** | Fixed in [hash]: [description] | Code change applied successfully |
| **Won't Fix** | Won't fix: [reason] | Valid comment but not addressing |
| **By Design** | By design: [explanation] | Current implementation is intentional |
| **Deferred** | Deferred to #[issue]: Will address in future | Creating issue for later |
| **Acknowledged** | Acknowledged: [note] | Noted but no action needed |

## 1. Fixed Template

Use when code changes have been applied.

### Qodo Format (Preferred for Qodo Comments)

```markdown
✅ **FIXED** in commit [hash]

**Changes:**
- [List of specific changes made]
- [Additional changes]

**Addressed:**
- [Sub-issue 1]
- [Sub-issue 2]
```

**Examples:**

```markdown
✅ **FIXED** in commit [76be991](https://github.com/owner/repo/commit/76be991)

**Changes:**
- Added validation to check all template variables are resolved
- Implemented fallback to nested path lookup when template incomplete
- Added logging for unresolved template variables

**Addressed:**
- Template placeholders no longer leak into output
- Fallback logic now executes when variables are missing
```

```markdown
✅ **FIXED** in commit [abc123f]

**Changes:**
- Exclude top-level key from extra_fields when using nested paths
- Updated excluded_keys logic to handle dot-notation mappings
- Prevents duplication of mapped values in extra_fields
```

### Standard Format

```markdown
Fixed in [commit-hash]: [brief description]

[Detailed explanation of changes made]

[For multi-issue comments, list all sub-issues:]
All issues addressed:
- ✅ [Sub-issue 1]
- ✅ [Sub-issue 2]
```

**Examples:**

```markdown
Fixed in abc123f: Prevent SQL injection vulnerability

Replaced string concatenation with parameterized queries and added input validation before database operations.

All issues addressed:
- ✅ SQL injection risk eliminated
- ✅ Input validation added
```

```markdown
Fixed in def456a: Add null check to prevent crash

Added null safety check before accessing data.items() to prevent NullPointerException when data is empty.
```

```markdown
Fixed in ghi789b: Improve variable naming for clarity

Renamed ambiguous variable names:
- ✅ `tmp` → `temporary_user_data`
- ✅ `x` → `max_retry_count`
- ✅ `cb` → `callback_function`
```

## 2. Won't Fix / Not Applicable Template

Use when a valid comment won't be addressed (rare - use sparingly).

### Qodo Format (Preferred for Qodo Comments)

```markdown
❌ **NOT APPLICABLE** - [Brief reason]

**Reasoning:**
- [Detailed explanation point 1]
- [Detailed explanation point 2]
- [Contextual justification]
```

**Examples:**

```markdown
❌ **NOT APPLICABLE** - Standard practice for search APIs

**Reasoning:**
- Query logging is essential for debugging, analytics, and search quality monitoring
- This is a **search API** - queries are the core data and not sensitive user information
- All modern search systems (Elasticsearch, Algolia, etc.) log queries for performance optimization
- No PII is contained in search queries in our use case
```

```markdown
❌ **NOT APPLICABLE** - Intentional design decision

**Reasoning:**
- This behavior follows the API specification in docs/api-spec.md Section 4.2
- Changing this would break backward compatibility with 15+ existing integrations
- Alternative approaches were evaluated in ADR-023 and rejected for performance reasons
```

### Standard Format

```markdown
Won't fix: [clear reason]

[Explanation of why this won't be addressed]
```

**Examples:**

```markdown
Won't fix: Intentional design decision

This behavior is intentional as per the API specification documented in docs/api.md. Changing this would break backward compatibility with existing clients.
```

```markdown
Won't fix: Framework limitation

This is a limitation of the underlying framework (Django 3.2). Upgrading the framework is planned for Q2 but out of scope for this PR.
```

## 3. By Design Template

Use when current implementation is intentional and correct.

**Format:**
```markdown
By design: [explanation of current approach]

[Context about why this design was chosen]
```

**Examples:**

```markdown
By design: Current implementation follows established patterns

This approach is consistent with the pattern used throughout the auth module. Refactoring this in isolation would create inconsistency. See similar implementation in auth/session.py:L45.
```

```markdown
By design: Performance trade-off for simplicity

While this could be optimized, the current approach prioritizes code readability and maintainability. Given the expected load (< 100 req/sec), the performance impact is negligible.
```

```markdown
By design: Error handling per specification

The current error handling follows the API specification (docs/api-spec.md Section 4.2) which requires throwing exceptions rather than returning error codes for this endpoint.
```

## 4. Deferred Template

Use when creating an issue to address the comment in the future.

**Format:**
```markdown
Deferred to #[issue-number]: Will address in future

[Explanation of why deferring and when it will be addressed]
```

**Examples:**

```markdown
Deferred to #456: Will address in performance optimization sprint

This refactoring will be included in the planned performance optimization work scheduled for Q2. Created issue for tracking. Thank you for the suggestion!
```

```markdown
Deferred to #789: Requires architectural discussion

This change impacts multiple modules and needs team discussion before implementation. Created issue and added to next architecture review agenda.
```

```markdown
Deferred to #321: Post-MVP enhancement

Valid suggestion! This improvement is out of scope for MVP but valuable for the next iteration. Tracked in backlog with "enhancement" label.
```

## 5. Acknowledged Template

Use when noting feedback but no specific action is needed.

**Format:**
```markdown
Acknowledged: [brief note]

[Any additional context if needed]
```

**Examples:**

```markdown
Acknowledged: Good catch on the edge case

Updated the test suite to include this scenario. While the current code handles it correctly, the additional test coverage is valuable.
```

```markdown
Acknowledged: Documentation updated

Added clarifying comments to explain the logic. The implementation remains unchanged but is now better documented.
```

```markdown
Acknowledged: Will monitor in production

Noted the potential edge case. Will monitor this in production and address if it becomes an actual issue. Added monitoring alert.
```

## Best Practices

### Professional Tone

- **No emojis** in replies (professional communication)
- **Be respectful** even when disagreeing
- **Explain reasoning** clearly and concisely
- **Thank reviewers** for valuable feedback

### Commit References

Always include commit hash for fixes:
```bash
COMMIT_HASH=$(git rev-parse --short HEAD)
echo "Fixed in ${COMMIT_HASH}: description here"
```

### Multi-Issue Comments

For comments with multiple issues, explicitly confirm all are addressed:

```markdown
Fixed in abc123f: Address all authentication issues

All issues addressed:
- ✅ SQL injection risk eliminated with parameterized queries
- ✅ Input validation added before database operations
- ✅ Error logging enhanced with security event tracking
- ✅ Rate limiting added to prevent brute force
```

### Issue References

When deferring, always create and link the issue:

```markdown
Deferred to #456: Performance optimization

Created issue to track this improvement. Will be addressed in the performance sprint planned for next quarter.
```

### Markdown Formatting

Use markdown for clarity:
- **Bold** for emphasis
- `Code` formatting for variable/function names
- Bullet lists for multiple items
- Line breaks for readability

## GitHub API Usage

Post replies using `--input -` for proper JSON handling:

```bash
gh api repos/{owner}/{repo}/pulls/comments/{comment_id}/replies \
  --input - <<EOF
{
  "body": "Fixed in ${COMMIT_HASH}: Prevent SQL injection vulnerability\n\nReplaced string concatenation with parameterized queries."
}
EOF
```

**Never use** `-f body=` as it can cause formatting issues with multiline content.

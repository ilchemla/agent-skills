# Severity Classification Guide

## Severity Levels

Comments are classified by severity to prioritize critical issues:

| Severity | Indicators | Priority | Commit Strategy |
|----------|-----------|----------|-----------------|
| **CRITICAL** | security, vulnerability, exploit, injection, XSS, SQL, authentication, authorization | Must fix first | Individual commits |
| **HIGH** | bug, error, crash, fail, broken, memory leak, race condition, deadlock | Should fix | Individual commits |
| **MEDIUM** | performance, optimization, refactor, code smell, technical debt, maintainability | Recommended | Batch into single commit |
| **LOW** | style, nit, formatting, typo, naming, whitespace, comment | Optional | Batch into single commit |

**Processing Order**: CRITICAL → HIGH → MEDIUM → LOW

## Classification Algorithm

When analyzing a comment, check for keywords in this order:

1. **CRITICAL keywords** → Classify as CRITICAL
2. **HIGH keywords** → Classify as HIGH
3. **MEDIUM keywords** → Classify as MEDIUM
4. **Otherwise** → Classify as LOW

## Examples

### CRITICAL Examples

```
"SQL injection vulnerability in user query"
→ CRITICAL (contains "SQL injection", "vulnerability")

"Missing authentication check allows unauthorized access"
→ CRITICAL (contains "authentication", "unauthorized")

"XSS vulnerability in comment rendering"
→ CRITICAL (contains "XSS", "vulnerability")
```

### HIGH Examples

```
"Null pointer exception when data is empty"
→ HIGH (contains "exception", implies crash/error)

"Memory leak in connection pool"
→ HIGH (contains "memory leak")

"Race condition in concurrent access"
→ HIGH (contains "race condition")
```

### MEDIUM Examples

```
"This function has O(n²) complexity, could be optimized"
→ MEDIUM (contains "optimized", performance concern)

"Consider refactoring this to reduce code duplication"
→ MEDIUM (contains "refactoring")

"Code smell: too many responsibilities in one class"
→ MEDIUM (contains "code smell")
```

### LOW Examples

```
"Variable name could be more descriptive"
→ LOW (naming suggestion)

"Missing newline at end of file"
→ LOW (formatting)

"Typo in comment: 'recieve' should be 'receive'"
→ LOW (typo)
```

## Multi-Issue Classification

For comments with multiple issues, use the **highest severity** among all sub-issues:

```
"SQL injection risk AND missing error logging"
→ CRITICAL (SQL injection is CRITICAL, even though logging is MEDIUM)

"Typo in variable name AND missing docstring"
→ LOW (both are LOW severity)
```

## Edge Cases

### Ambiguous Keywords

If a comment contains ambiguous terms:
- **Default to MEDIUM** if unsure between HIGH/MEDIUM
- **Ask user** for clarification if critically ambiguous
- **Better to over-classify** (higher severity) than under-classify

### Context Matters

Consider the context of the code:
- Authentication/authorization code → Lean toward CRITICAL
- Public API endpoints → Higher severity
- Internal utilities → Can be lower severity
- Test files → Usually MEDIUM/LOW unless breaking tests

### False Positives

Some comments may contain severity keywords but not be that severe:

```
"Add test for error handling"
→ MEDIUM (not HIGH despite "error" keyword - it's about tests)

"Comment should explain the security model"
→ LOW (not CRITICAL despite "security" - just about documentation)
```

Use judgment and context to avoid false positives.

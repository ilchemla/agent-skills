# Return contract (all reviewers)

Write your findings file in this shape:

```
# <role> findings

## Findings
### F1 [P0|P1|P2] <short title>
- where: <file:line | doc section | message paragraph>
- evidence: <exact quote or command output that shows it>
- why it matters: <the concrete consequence, one line>
- fix: <the smallest change that resolves it>
- confidence: 50 | 75 | 100

(repeat; or write "No findings." )

## Out of lane
- <one line each, optional>

## Not checked
- <what you did not or could not verify, and why; web fallback used, if any>
```

## Severity
- **P0:** wrong result, broken behavior, data loss, security exposure, a false claim to a customer/partner, or missing the core of what was asked. Must fix before shipping.
- **P1:** real problem a user, reader or maintainer will hit; meaningful simplification; misleading wording; missing test for changed behavior. Should fix now.
- **P2:** worthwhile improvement, low risk. Fix if cheap.

## Confidence (by what you actually did)
- **100:** reproduced or directly confirmed (ran it, read the exact line, checked the live source).
- **75:** strong evidence with a concrete, named consequence; you quote the exact line.
- **50:** plausible but not confirmed. Report only if P0.
- Below 50: do not report.
A finding at 75 or 100 without a quoted `evidence` line is treated as 50.

## Not findings
- Problems that existed before this work and were not touched by it.
- Anything a linter or formatter would catch.
- Pure style or taste preferences.
- Disagreeing with a settled decision (raise it under "Out of lane" as an open question instead).
- Generic advice ("consider adding more tests") without a specific gap.

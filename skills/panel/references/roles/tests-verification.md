# Role: tests-verification

## Checklist
1. Does every changed behavior have a test that would fail if the behavior broke? Name the gap precisely (function, case).
2. For bug fixes: is there a test that fails before the fix and passes after?
3. Are the tests meaningful? Flag mocks that bypass the code under test, assertions that cannot fail, tests that only check that the code ran.
4. Run the relevant tests if cheap (follow the repo's CLAUDE.md/AGENTS.md for how). Report actual results.
5. Over-test-engineering is also a defect: duplicated tests, many tests for one behavior, heavy fixtures for trivial checks.
6. For evals and data pipelines: is there a check that the numbers are right, not just that the job finished?

## Lane
Verification quality. Do not re-review the logic itself.

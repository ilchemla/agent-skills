# Test Integration Guide

## Overview

Automatically detect and run project tests before pushing changes to ensure fixes don't break existing functionality.

## Test Command Detection

### Detection Order

1. Check `package.json` for Node.js projects
2. Check `pyproject.toml` for Python projects
3. Check `Makefile` for Make-based projects
4. Check for language-specific config files

### Node.js / JavaScript

```bash
# Check package.json
if test -f package.json; then
  TEST_CMD=$(jq -r '.scripts.test // empty' package.json)
  LINT_CMD=$(jq -r '.scripts.lint // empty' package.json)
  FORMAT_CMD=$(jq -r '.scripts.format // empty' package.json)
fi

# Common commands
npm test
npm run test
npm run lint
npm run format
```

### Python

```bash
# Check pyproject.toml
if test -f pyproject.toml; then
  grep -q "\[tool.pytest\]" pyproject.toml && TEST_CMD="pytest"
  grep -q "\[tool.black\]" pyproject.toml && FORMAT_CMD="black ."
  grep -q "\[tool.ruff\]" pyproject.toml && LINT_CMD="ruff check ."
fi

# Common commands
pytest
pytest -v
python -m pytest
ruff check .
black .
mypy .
```

### Go

```bash
# Go projects
if test -f go.mod; then
  TEST_CMD="go test ./..."
  LINT_CMD="golangci-lint run"
  FORMAT_CMD="go fmt ./..."
fi
```

### Rust

```bash
# Rust projects
if test -f Cargo.toml; then
  TEST_CMD="cargo test"
  LINT_CMD="cargo clippy"
  FORMAT_CMD="cargo fmt"
fi
```

### Makefile

```bash
# Check Makefile
if test -f Makefile; then
  grep -q "^test:" Makefile && TEST_CMD="make test"
  grep -q "^lint:" Makefile && LINT_CMD="make lint"
  grep -q "^format:" Makefile && FORMAT_CMD="make format"
fi
```

## Running Tests

### Basic Test Execution

```bash
# Run detected test command
if [ -n "$TEST_CMD" ]; then
  echo "Running tests: $TEST_CMD"
  $TEST_CMD
else
  echo "Warning: No test command detected"
fi
```

### With Output Capture

```bash
# Capture test output
TEST_OUTPUT=$(mktemp)
if $TEST_CMD > "$TEST_OUTPUT" 2>&1; then
  echo "✅ All tests passed"
  TESTS_PASSED=true
else
  echo "❌ Tests failed"
  cat "$TEST_OUTPUT"
  TESTS_PASSED=false
fi
rm "$TEST_OUTPUT"
```

### Test Result Parsing

```bash
# Parse test results
if $TEST_CMD 2>&1 | tee test_output.txt; then
  # Extract pass/fail count
  PASSED=$(grep -o "[0-9]* passed" test_output.txt | awk '{print $1}')
  FAILED=$(grep -o "[0-9]* failed" test_output.txt | awk '{print $1}')
  echo "Results: ${PASSED} passed, ${FAILED} failed"
fi
```

## CI Check Fixing

### Lint Fixing

```bash
# Auto-fix lint issues
if [ -n "$LINT_CMD" ]; then
  # Try with --fix flag
  if [[ "$LINT_CMD" == *"eslint"* ]]; then
    npm run lint -- --fix
  elif [[ "$LINT_CMD" == *"ruff"* ]]; then
    ruff check --fix .
  elif [[ "$LINT_CMD" == *"golangci-lint"* ]]; then
    golangci-lint run --fix
  fi
fi
```

### Format Fixing

```bash
# Auto-format code
if [ -n "$FORMAT_CMD" ]; then
  echo "Formatting code: $FORMAT_CMD"
  $FORMAT_CMD

  # Check if any files changed
  if ! git diff --quiet; then
    echo "Code formatted, files changed"
    git add -u
  fi
fi
```

## Test Failure Handling

### Failure Analysis

When tests fail after applying fixes:

1. **Check if test is related to changes**
   ```bash
   git diff HEAD~1 --name-only | grep -q test/
   ```

2. **Analyze test output**
   - Look for specific test names
   - Check error messages
   - Identify affected modules

3. **Determine action**
   - Fix related to change → Attempt fix
   - Unrelated → May be pre-existing
   - Unclear → Ask user

### User Decision Prompt

```markdown
Tests failed after applying fixes:

Failed tests:
- test/auth.test.js: test_null_handling (new failure)
- test/api.test.js: test_response_format (pre-existing)

Options:
1. Retry - Review test output and try again
2. Fix tests - Attempt to fix failing tests
3. Skip tests - Continue without passing tests (NOT recommended for CRITICAL/HIGH)
4. Abort - Rollback changes
```

### Severity-Based Test Requirements

| Severity | Test Requirement |
|----------|------------------|
| CRITICAL | MUST pass - no exceptions |
| HIGH | MUST pass - no exceptions |
| MEDIUM | Should pass - can skip with warning |
| LOW | Optional - can skip for style fixes |

### Retry Logic

```bash
MAX_TEST_RETRIES=2
for i in $(seq 1 $MAX_TEST_RETRIES); do
  if $TEST_CMD; then
    echo "✅ Tests passed on attempt $i"
    break
  else
    if [ $i -lt $MAX_TEST_RETRIES ]; then
      echo "Retry $i/$MAX_TEST_RETRIES..."
      sleep 2
    else
      echo "❌ Tests failed after $MAX_TEST_RETRIES attempts"
      exit 1
    fi
  fi
done
```

## Best Practices

### Before Running Tests

```bash
# Ensure code is formatted
if [ -n "$FORMAT_CMD" ]; then
  $FORMAT_CMD
fi

# Fix lint issues
if [ -n "$LINT_CMD" ]; then
  $LINT_CMD --fix 2>/dev/null || true
fi

# Then run tests
$TEST_CMD
```

### Test Output Management

```bash
# Verbose for debugging
$TEST_CMD --verbose

# Quiet for CI
$TEST_CMD --quiet

# With coverage
$TEST_CMD --coverage
```

### Timeout Handling

```bash
# Set timeout for tests
timeout 300 $TEST_CMD || {
  echo "Tests timed out after 5 minutes"
  exit 1
}
```

## Common Issues

### No Test Command Found

```bash
if [ -z "$TEST_CMD" ]; then
  echo "⚠️  Warning: No test command detected"
  echo "Common locations checked:"
  echo "  - package.json (scripts.test)"
  echo "  - pyproject.toml ([tool.pytest])"
  echo "  - Makefile (test target)"
  echo ""
  echo "Please specify test command or skip tests for this PR"
fi
```

### Tests Fail Due to Missing Dependencies

```bash
# Ensure dependencies installed
if test -f package.json && ! test -d node_modules; then
  echo "Installing dependencies..."
  npm install
fi

if test -f requirements.txt; then
  pip install -r requirements.txt
fi
```

### Environment-Specific Failures

```bash
# Set test environment variables
export NODE_ENV=test
export TESTING=true
export DEBUG=false

# Run tests
$TEST_CMD
```

## Integration with Workflow

### In Execute Phase

```
1. Detect test commands
2. Apply code fixes
3. Format code
4. Fix lint issues
5. Run full test suite ← Critical step
6. If tests pass → Push
7. If tests fail → Handle appropriately
```

### Example Workflow

```bash
# Phase 3: Execute
echo "Detecting project configuration..."
detect_test_commands

echo "Applying fixes..."
apply_code_fixes

echo "Fixing CI checks..."
fix_lint_issues
fix_format_issues

echo "Running test suite..."
if run_tests; then
  echo "✅ All tests passed"
  git push origin HEAD
else
  echo "❌ Tests failed"
  handle_test_failure
fi
```

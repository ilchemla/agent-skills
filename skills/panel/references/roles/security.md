# Role: security

## Checklist
1. **Secrets:** keys, tokens, passwords, internal URLs in code, configs, logs, docs, or messages. Check `git diff` including new files and fixtures.
2. **Auth and permissions:** missing or bypassable checks, privilege escalation, tenancy leaks between customers.
3. **Injection:** user input reaching SQL, shell, HTML, prompts (prompt injection for LLM features), file paths, URLs (SSRF).
4. **Data exposure:** PII or customer data in logs, errors, analytics, public artifacts.
5. **Private context leaking:** internal names, customer names, deal terms, or internal links in anything shared externally or posted to shared docs or public repos.
6. **Dependencies:** new packages: are they well known and pinned?

Severity: externally exploitable or leaks secrets/customer data = P0.

## Lane
Security and privacy only.

# Roster: picking the panel

Pick on **evidence in the work**, not keywords. Each extra role must cover a distinct risk the others would miss. 3-5 roles is normal; 6 is the cap.

## Always
| Role | Why |
|---|---|
| `intent-correctness` | Does it do what was asked, correctly and completely, including edge cases. |
| `simplifier` | Duplication, staleness, over-engineering, word count. |

## Default-on when the condition holds
| Role | Include when | Skip when |
|---|---|---|
| `product-gtm` | Anything a user, customer, buyer or stakeholder will see, or that shapes the product: features, APIs/SDKs, public docs, PRDs, specs, roadmaps, pricing, positioning, launch plans, announcements, customer emails. | Purely internal work (refactors, infra, CI, internal tooling, team process). State the skip. |
| `fresh-reader` | There is prose someone will read (docs, specs, plans, emails, chat posts, READMEs, PR descriptions, release notes) or a UI. | Pure code with no user-facing text. |
| `visual-design` | The artifact is visual: slides or a deck, a diagram or chart, a PDF layout, an HTML page, a UI, an image. Needs rendered views (see SKILL.md Step 1). | Text-only work with no layout (code, plain markdown, chat messages). |

## On evidence
| Role | Include when |
|---|---|
| `skeptic` | Risky area or a bet: auth, payments, data writes/deletes, migrations, CI or test gates that could silently pass, success metrics a decision rests on, commitments to customers, partners or execs. |
| `security` | Secrets, auth, tokens, permissions, user input reaching queries/shell/HTML/prompts, PII, or a shared/public artifact that could leak private context. |
| `tests-verification` | Code changed and there are (or should be) tests; bug fixes (is there a failing test first?); evals, experiments or metrics that must be trustworthy. |
| `fact-checker` | The work makes factual claims: numbers, benchmarks, competitor facts, quotes, customer feedback, what a system does. |
| `domain-expert` | A specialty the others lack. Fill in the domain. Examples: "API design", "web frontend performance", "data pipeline and SQL correctness", "LLM prompt and agent design", "B2B SaaS pricing and packaging", "product analytics and experiment design". At most 2. |

## Typical panels
| Work | Panel |
|---|---|
| Backend code change | intent-correctness, simplifier, tests-verification, + security/skeptic on evidence, + product-gtm if the API surface changes |
| Public SDK / API feature | intent-correctness, simplifier, product-gtm, tests-verification, domain-expert (API design) |
| PRD / spec / plan | intent-correctness, simplifier, product-gtm, fresh-reader, skeptic |
| Roadmap / strategy / business case | intent-correctness, product-gtm, skeptic, fact-checker, simplifier |
| Research doc / competitive analysis | intent-correctness, fact-checker, product-gtm, domain-expert, simplifier |
| Email, chat message, announcement | intent-correctness, product-gtm, fresh-reader, simplifier (+ fact-checker if it states facts) |
| Data pipeline / metrics / dashboard | intent-correctness, domain-expert (data or analytics), skeptic, simplifier |
| Slide deck | intent-correctness, simplifier, visual-design, product-gtm, fresh-reader |
| Diagram | intent-correctness, simplifier, visual-design, domain-expert |
| Branded PDF / report | intent-correctness, simplifier, visual-design, fresh-reader, fact-checker |

## Learnings adjustments
Check `~/.claude/panel/learnings.md`. An optional role with no accepted findings in its last 5 runs on this work type can be skipped; say so in the announcement. Never auto-skip the always-on roles (`intent-correctness`, `simplifier`), and never auto-skip `security` or `skeptic` when their condition holds.

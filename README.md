# agent-skills

Claude Code skills I use every day.

| Skill | What it does |
|---|---|
| [`panel`](skills/panel/SKILL.md) | At the end of a task, a panel of expert subagents reviews what you just did and gives you one prioritized fix list. |
| [`tldr`](skills/tldr/SKILL.md) | When Claude's answer is too long, get the bottom line, or go through its questions one at a time. |
| [`qodo-pr-resolver`](skills/qodo-pr-resolver/SKILL.md) | Works through Qodo PR review comments: analyze, confirm, fix, resolve. |

## Install
```bash
npx skills add ilchemla/agent-skills --skill panel --skill tldr -g -a claude-code
```
Or copy by hand: `mkdir -p ~/.claude/skills && cp -R skills/panel skills/tldr ~/.claude/skills/`. Start a new Claude Code session afterwards.

## panel
Run `/panel` (or say "review what we did with a team of experts") when you finish something: code, a spec, a plan, a doc, a message.

- It picks 3 to 6 reviewers for *this* work instead of a fixed pipeline. Correctness and a simplifier always sit on the panel. Product, visual design, security, skeptic, tests, fact-checker, fresh reader or a domain expert join when the work calls for it.
- For slides, diagrams, PDFs and web pages it renders them to images first, so reviewers judge what people will see, not the source.
- It checks every important finding against the source before showing it to you.
- You get a verdict (ship, fix-first or rethink), a P0/P1/P2 table, and what the panel did not check. It asks before applying anything.

```
Panel (4): intent-correctness, simplifier, product-gtm (new public API), security (API keys).
Verdict: fix-first. P0-1 API key logged on error (security) · P1-1 two helpers do the same thing (simplifier)
Apply all P0+P1?
```

Good to know:
- A run spawns 3 to 6 subagents, so it costs more than a normal reply. `--quick` caps it at 3 on a smaller model.
- The first run reads your local `~/.claude/CLAUDE.md`, memory and enabled plugins to learn your context, asks you up to 3 questions, and saves the result to `~/.claude/panel/`. The file stays on your machine; Claude reads it like any other context.
- Reviewers are told to stay read-only; that is an instruction, not a sandbox.
- Web lookups use the [Nimble CLI](https://www.npmjs.com/package/@nimble-way/nimble-cli) if installed, else Claude's built-in web search.

## tldr
For when Claude sends a wall of text and you are lost. It changes *how Claude talks to you*; it is not a token saver or a persona.

- `tldr?` gives one bold line, at most 3 bullets, and what is needed from you.
- `one by one` asks its open questions one at a time, recommended answer first, with a progress line.
- `i don't understand X` explains just X, in plain words with one example.

```
You: tldr?
Claude: **Go with usage-based pricing.**
- cheapest to launch
- matches how competitors charge
3 decisions: tier names, launch date, discount policy. One by one?
```

Optional always-on mode keeps every reply short without asking. It is off by default and needs a one-time hook; see the [skill file](skills/tldr/SKILL.md#optional-always-on-gentle-mode). Then `/tldr on` and `/tldr off`.

## License
MIT

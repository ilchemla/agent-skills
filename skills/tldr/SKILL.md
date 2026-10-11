---
name: tldr
description: >-
  Be gentle with a human's attention. Collapses the last reply to its bottom
  line, explains a confusing term in plain words, or walks through open
  questions one at a time with a recommendation each. Also switches an
  optional always-on gentle mode on or off. Use when the user says "tldr",
  "tldr?", "bottom line", "too long", "too much", "i'm lost", "i don't
  understand", "one by one", "one at a time", "too many questions", or runs
  `/tldr on` / `/tldr off`.
argument-hint: "[on | off | one-by-one | explain <term>]"
---

# tldr: gentle with a human's brain

The user is a human with limited focus, not an AI. When a reply loses them, the fix is never a slightly shorter version of the same thing. It is the answer, in plain words, and one decision at a time.

Do not announce the mode, do not say "in short" or "briefly", and do not apologize at length. Just be short.

## Pick the mode from what they said
| They said | Mode |
|---|---|
| `/tldr`, "tldr?", "bottom line", "too long", "too much" | Bottom line |
| "i don't understand X", "what is X", "i'm lost" | Explain |
| "one by one", "one at a time", "too many questions", or the bottom line has 2+ decisions | One by one |
| `/tldr on` / `/tldr off` | Toggle |

## Bottom line
Rewrite the previous reply (or the current state of the work) as:
```
**<the answer or verdict in one line>**
- <what they need to know>
- <at most 3 bullets, ~80 words total>
<Nothing needed from you.> or <N decisions: A, B, C. One by one?>
```
- Hit the target on the first try. A second "tldr?" means it failed.
- Plain words. No headings, no tables, no code unless the answer is code.
- Lead with the answer, not with a position ("one correction first", "your instinct is right, but").
- Name things, never count them: "Post A, B, C", not "three things".
- Jargon only with a few plain words next to it, or not at all.
- Keep any warning about something destructive or irreversible. Never cut that.

## Explain
They did not understand a term or idea.
- About 100 words. Plain words, one concrete example or analogy from their own work (their product, their codebase, the current task).
- Explain only that thing. Do not restate the whole previous answer.
- End with one short line linking it back to the decision at hand, not "does that make sense?".

## One by one
1. **Collect** every open question and decision from the conversation, including ones buried in long replies.
2. **Remove** what you can answer yourself by looking it up (code, files, docs, tools). Facts are your job; only decisions are theirs. Drop the ones that do not matter.
3. **Order** so a question that depends on another comes after it. Most important first otherwise.
4. Say it once, in one line: `4 decisions: A, B, C, D. Starting with A.`
5. **Ask one per turn** with AskUserQuestion: 2-4 concrete options, the recommended one first labeled "(Recommended)", each description 10 words or fewer. Phrase it so picking the first option accepts your recommendation. If the question depends on a draft or text they must read, print it in chat first (the question box can hide long text).
6. After each answer, one progress line, then the next question: `Q2 of 4 · settled: A = keep the deadline`.
7. When done, a 3-line summary of what was decided, then act on it. Do not ask "anything else?".

If an answer opens a new question, add it to the end of the queue and update the count.

## Optional: always-on gentle mode
The short rules in `${CLAUDE_SKILL_DIR}/gentle.md` can be injected into every prompt by a `UserPromptSubmit` hook, so Claude stays brief without being asked. It is off by default and needs a one-time hook in `~/.claude/settings.json`:
```json
{
  "hooks": {
    "UserPromptSubmit": [
      { "hooks": [ { "type": "command",
        "command": "[ -f ~/.claude/.tldr-gentle ] && cat ~/.claude/skills/tldr/gentle.md || true" } ] }
    ]
  }
}
```
The path assumes this skill is installed at `~/.claude/skills/tldr/`. Merge into existing hooks rather than replacing them.

Toggles:
- `/tldr on`: first check that `~/.claude/settings.json` contains `tldr-gentle`. If it does not, say the hook is missing, show the snippet above, and offer to add it. Only after the hook exists: `mkdir -p ~/.claude && touch ~/.claude/.tldr-gentle`, then reply `Gentle mode on. Takes effect on your next message.`
- `/tldr off`: `rm -f ~/.claude/.tldr-gentle`, then reply `Gentle mode off.`

## Learn
If they say "tldr?", "still too long" or "i don't understand" right after a tldr reply, it missed. Append one line to `~/.claude/tldr/learnings.md` (create the folder and file if missing): date, mode, what they said, what was too much (length, jargon, number of bullets). On the second miss of the same kind, **propose** a concrete tightening of the matching rule here or in `gentle.md`, and apply it only after the user approves.

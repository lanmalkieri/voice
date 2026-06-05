# Example learning (format reference)

Real learnings are written to `~/.claude/voice/learnings/` at runtime and are gitignored. They live next to the skill, not inside this repo. This file just shows the shape of one so you know what the skill writes.

Each learning is one short, behavior-changing note. Filename: `<YYYY-MM-DD>-<slug>.md`, for example `2026-06-05-no-tack-on-closers.md`.

```markdown
---
date: 2026-06-05
trigger: "user said: stop adding a summary sentence that restates the point"
---
Do: end on the concrete point.
Avoid: a closing sentence that restates it in vaguer or grander terms.
Bad: "The skill reads it on every write. Your voice sharpens with use instead of drifting."
Good: "The skill reads it on every write."
```

The skill reads every note in `~/.claude/voice/learnings/` before it drafts, and treats them as recent overrides on top of your compiled profile.

---
name: Voice
description: Writes, rewrites, edits, and reviews any writing in the user's own voice, and builds and maintains that voice profile. Use when drafting or polishing emails, messages, posts, docs, marketing, sales copy, executive comms - or when the user wants to set up, update, or apply their personal writing voice. Strips AI-style tells, applies craft rules, and writes as them. Trigger on /voice, "build my voice", "write this in my voice", or any drafting, editing, or reviewing request. Also captures wording feedback like "I don't like how this is worded" as learnings it reads on future writes.
---
# Voice

One skill that builds the user's writing voice and writes in it. Every piece of writing gets three passes: strip the AI fingerprint (`tells.md`, enforced by `check.py`), apply craft (`craft.md`), and write in the user's voice (`~/.claude/voice/about-me.md`). The voice itself is built through an interview.

## Files
- `tells.md` — the AI fingerprint to strip. The floor.
- `craft.md` — how to write well: lead with the point, match length to the job, keep a pulse.
- `check.py` — deterministic gate. Run before delivery.
- `build.md` — the builder: samples, depth, interview, archive, compile.
- `agents/sample-analyst.md` — agent brief: reads writing samples, returns style findings.
- `agents/compiler.md` — agent brief: turns the archive into the compact about-me profile.
- `agents/critic.md` — agent brief: judges a draft against the voice profile, returns fixes.

## State (in `~/.claude/voice/`)
- `voice-profile.md` — the full archive: interview verbatim plus sample findings.
- `about-me.md` — the compact compiled profile. The voice layer the writer reads.
- `interview-progress.md` — transient, exists only while an interview is mid-flight.
- `learnings/` — short, dated correction notes captured as you give feedback. Read on every write.

The agents analyze and judge only. The main thread runs the interview, drafts, and writes every file. Subagents can fail silently on writes, so keep writes here.

## The one rule
Every sentence must earn its place. It earns it by carrying information (a fact, a number, a decision, evidence, a next action) or, in writing meant to be read for its own sake, by doing real work: moving the piece, building a concrete image, setting rhythm, holding tension, landing a real opinion. Validation, warmup, throat-clearing, an inflated word standing in for a fact, decoration with no work: cut everywhere. The lists in `tells.md` and `check.py` are the floor. This rule is the ceiling.

## Route by intent

Read the request and pick one.

### Write
Drafting, rewriting, editing, polishing, replying: any text to produce or improve.
1. If `~/.claude/voice/about-me.md` is missing, run Build first, then return here. Exception: if the user says skip voice or just write it, draft with `tells.md` and `craft.md` only, and tell them the voice layer is off.
2. Read `tells.md`, `craft.md`, `about-me.md`, and every note in `~/.claude/voice/learnings/`.
3. Draft in this thread, with full conversation context, under the one rule plus tells plus craft plus voice plus learnings. Learnings are recent, specific overrides: where one conflicts with the profile or a craft default, the learning wins.
4. Run `check.py`. Fix until it prints PASS.
5. For anything substantial or outward-facing (more than a few lines, or going to someone outside), spawn the `critic` agent with the draft, `about-me.md`, and `tells.md`. Apply its fixes, re-run `check.py`.
6. Output only the final text. Don't mention the rules or the scan unless asked.

### Build
"Build my voice", "set up my voice", `/voice build`, or any Write request when no profile exists. Run `build.md`.

### Review
"Does this sound like me", "review this in my voice", "check this". Spawn the `critic` agent and run `check.py`. Return the verdict and the concrete fixes, plus the corrected version if they want it.

### Sample
`/voice sample`, "add a writing sample", "here's something I wrote", or a pasted dump of the user's own writing to learn from. This is how the user feeds real writing into the profile.
1. Collect the samples: inline pasted text, file paths, a folder, or URLs. If they ran `/voice sample` with nothing attached, ask them to paste the text or give paths now.
2. Spawn the `sample-analyst` agent (Agent tool, foreground) with the brief in `agents/sample-analyst.md` plus the samples. It returns style findings.
3. Fold the findings in:
   - **Profile exists:** append or update the "Writing-sample analysis" section of `voice-profile.md`, then spawn `compiler` to rewrite `about-me.md` so the sample-derived laws and phrases land in the voice layer. Where a sample finding conflicts with an interview answer, keep both and flag it as a productive contradiction.
   - **No profile yet:** seed a new `voice-profile.md` from the findings (Core identity + Writing-sample analysis + Quick reference), then spawn `compiler` to write `about-me.md`. This bootstraps a voice from writing alone, no interview required. Offer `/voice` afterward to deepen it with the interview.
4. Confirm what changed: the new laws, phrases, and tells pulled from the sample.

### Learn
The user pushes back on wording ("I don't like how this is worded", "too formal", "don't open like that", "stop saying X"), states a standing preference ("I prefer Y", "always do Z", "never do W"), or runs `/voice learn [note]`. This is how the voice sharpens through use.
1. Capture it as ONE short, behavior-changing note. Create `~/.claude/voice/learnings/` if needed, then write `<YYYY-MM-DD>-<slug>.md` containing: the rule (do / avoid), the trigger that prompted it, and a bad/good pair pulled from the actual exchange when there is one.
2. Keep it specific and additive. If a new note contradicts an old one, the newer wins: update or delete the stale file.
3. Confirm in one line what you captured.

When the user reacts against something you just wrote, capture the lesson without being asked, then apply it in the rewrite. Fold durable learnings into `about-me.md` on `/voice recompile` or `/voice extend`, then prune their files so the list stays short.

### Manage
- `view` — print `about-me.md`.
- `refresh` — move the old files to `voice-profile.<date>.bak.md` and `about-me.<date>.bak.md`, then run Build from scratch.
- `extend` — run another interview round per `build.md`, append to the archive, recompile.
- `recompile` — spawn `compiler` on the existing archive, rewrite `about-me.md`.
- `status` — report which files exist and when they were built.

## Argument
- `/voice quick` runs the ~25-question build, `/voice full` runs the ~100. Otherwise the builder asks.
- `/voice sample [paths or pasted text]` analyzes your writing and folds it into the profile (see the Sample intent). Works with or without an existing profile.
- `/voice learn [note]` records a correction or preference (see the Learn intent). You rarely need it by hand; just say what you do not like and it gets captured.

## Deterministic check
```bash
printf '%s' "$BODY" | python3 ~/.claude/skills/voice/check.py
```
A draft that prints FAIL does not ship until it prints PASS. Add `--no-llm` to skip the LLM judge. `tells.md` and `craft.md` still apply where the script cannot see. Words and phrases the user legitimately writes live in `~/.claude/voice/allowlist.txt` (one per line, `#` for comments); the static gate and the LLM judge both skip them, so a real person's vocabulary and signature phrases survive the floor.

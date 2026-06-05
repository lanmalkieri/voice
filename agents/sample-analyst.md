# Sample-analyst agent (brief)

Spawned by `build.md` (step 2) and by the Sample intent (`/voice sample`). Spawn it with the Agent tool, foreground, so it can prompt if it needs to read a file. Pass everything below plus the samples: pasted text, and any file paths or URLs to read. It analyzes only and returns text. It does not write files.

## Task for the agent
You are analyzing writing samples to extract how this specific person writes, so another model can imitate them. Read everything provided. Look at how it is written, not what it is about. Then return a structured findings report.

Report on each of these, with at least one short verbatim quote as evidence per point:

1. **Sentence rhythm.** Typical length. How much it varies (burstiness). Short punches mixed with long builds, or even cadence? Quote a representative run.
2. **Openers.** How they start pieces and paragraphs. Straight in, or context first? Quote two real openings.
3. **Closers.** How they end. Quote one or two.
4. **Word choice.** Register (casual, plain, technical, formal). Recurring favorite words and constructions. Words or registers they clearly avoid.
5. **Punctuation and formatting.** Commas, parentheses, dashes, colons, line breaks, lists, bold, casing. Note anything distinctive (heavy parentheticals, fragments, all-lowercase, no Oxford comma).
6. **Verbal tics and signature phrases.** Exact phrases, transitions, or moves that repeat. Quote them.
7. **Stance and personality.** How opinionated. How direct or hedged. Humor (type, or none). How they handle disagreement, praise, uncertainty.
8. **Structure.** How they organize an argument. Top-down or build-to-it. Use of headers and lists. Default shape.
9. **Tells to preserve.** Hard-to-fabricate specifics, asides, self-corrections, dated references, mixed feelings: the human signals that make it unmistakably them. Quote examples.
10. **Range.** Where the voice shifts by context (terse in Slack, expansive in essays). Name the trigger for each register.

End with a list titled **"For the voice profile"**: 8 to 15 one-line, behavior-changing rules in imperative form. Examples: "Open cold, no preamble." "Use parentheses for the real opinion." "Never hedge a recommendation."

Return only the findings report. Do not write any files. Do not rewrite the samples.

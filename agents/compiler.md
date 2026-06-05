# Compiler agent (brief)

Spawned by `build.md` (step 6), `/voice extend`, and `/voice recompile`. Spawn it with the Agent tool, foreground. Pass this brief plus the full `voice-profile.md`. It returns the about-me content as text. The main thread writes it to `~/.claude/voice/about-me.md`.

## Task for the agent
Turn the voice archive into the compact standing-context profile that other tools read at the start of a session. This file is not for humans. It is for a model to read so it writes, edits, judges, and decides more like this person. Do not summarize the person. Preserve the smallest set of instructions, examples, phrases, laws, refusals, and taste signals that change behavior.

### Core rule
Every line must pass this test: if it disappeared, would the model write, edit, judge, refuse, structure, or decide differently? If yes, keep it. If no, cut it. Optimize for behavioral fidelity per token.

### Length
2,000 to 4,000 tokens typical. Hard ceiling 5,000. Shorter is fine if the archive is thin. Longer only if every line is high-signal. Do not pad. Do not cut useful specificity to look minimal.

### Keep
Specific voice, writing, and communication laws. Hard refusals. Compact bad/good examples. Verbatim phrases that teach how they sound. Words they use, words they hate. Sentence shapes. Taste loves and disgusts. Decision rules. Small tells. Productive contradictions. Identity that affects voice or judgment.

### Cut
Generic values. Flattering self-description. Biography that doesn't affect output. Aspirations with no evidence. Repeated ideas. Vague preferences. Long transcript excerpts. Quotes that are true but don't change output.

### Apply the writing tells to this file
The prose follows the writing rules: no em dashes, no validation filler, no inflated vocabulary, no formula patterns. A voice file that reads like AI defeats its purpose.

### Output
Return the full markdown content for `about-me.md`, body in this structure. Fill every section from the archive. Drop a section only if the archive has nothing for it. Return only the file content, no commentary.

```markdown
# About me (voice profile)

<usage>
Three compact lines on how to use this file when writing, editing, or judging as this person.
</usage>

<priority>
1. Current user instructions override this file.
2. Truth, safety, and the task override style imitation.
3. Hard refusals override ordinary preferences.
4. Specific examples override abstract rules.
5. Evidence-backed rules override inferred ones.
6. On conflict, preserve deeper judgment over surface style.
</priority>

<identity_context>
Only identity that affects voice, taste, metaphors, judgment, or recurring concerns.
</identity_context>

<voice_fingerprint>
Operational description of the voice: rhythm, density, directness, humor, emotional temperature, formality, weirdness, default stance. No generic adjectives unless tied to observable behavior.
</voice_fingerprint>

<writing_laws>
<law>Do: [specific]. Avoid: [specific failure]. Example: [optional compact example].</law>
</writing_laws>

<communication_laws>
Rules for emails, replies, requests, disagreement, praise, critique, reminders, apologies, refusals.
</communication_laws>

<hard_refusals>
<never>Never [specific]. Bad: "[bad]". Use: "[better]".</never>
</hard_refusals>

<taste_loves>
Specific things they admire, trust, gravitate toward. Add why only when it changes output.
</taste_loves>

<taste_disgusts>
Specific things they reject: words, tropes, styles, arguments, postures, formats.
</taste_disgusts>

<phrase_bank>
<use>Words, phrases, metaphors, sentence shapes, jokes, transitions that sound like them.</use>
<avoid>Words, structures, tones, claims that do not sound like them.</avoid>
</phrase_bank>

<signature_tells>
Small recurring details that make their writing recognizable and can guide future output.
</signature_tells>

<decision_rules>
How they judge quality, usefulness, honesty, risk, trust, competence, bullshit, and whether something is worth saying.
</decision_rules>

<productive_contradictions>
<tension>[tension]. Preserve by: [operational instruction].</tension>
</productive_contradictions>

<golden_examples>
Three to six only. Each teaches a high-value pattern.
<example>
<context>[when this applies]</context>
<bad>[does not sound like them]</bad>
<good>[sounds like them]</good>
<why>[short]</why>
</example>
</golden_examples>

<do_not_infer>
Things not to assume about them from this profile.
</do_not_infer>

<final_instruction>
One line: apply this profile silently unless the user overrides it.
</final_instruction>
```

### Before returning, audit silently
Cut generic, flattering, weak-biography, and low-evidence lines. Cut quotes that don't change output. Keep specific examples, negative constraints, positive taste, decision rules, useful contradictions. Stay under 5,000 tokens.

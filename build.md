# Build the voice profile

Capture how this person thinks, writes, and judges precisely enough that the writer can produce text they would not flinch at. Output is two files: the full archive (`voice-profile.md`) and the compact profile the writer reads (`about-me.md`).

The main thread runs this. Two agents help and return content for you to write: `agents/sample-analyst.md` analyzes samples, `agents/compiler.md` compiles the archive.

## Steps
1. Create `~/.claude/voice/` if it does not exist.
2. **Samples.** Ask: "Do you have writing that sounds like you? Paste a few hundred words, give me file paths or URLs, or say skip. Emails you're proud of, a post, a Slack rant, a doc, anything." If they provide samples, spawn the `sample-analyst` agent (Agent tool, foreground) with the brief in `agents/sample-analyst.md` plus the samples. Hold its findings for steps 5 and 6. If they skip, continue; they can add samples later with `/voice sample`.
3. **Depth.** If the argument did not set it, ask: quick (~25 questions, one sitting) or full (~100, can span sessions).
4. **Interview.** Run the protocol below, one question at a time. After every 3 to 5 answers, write the running transcript to `~/.claude/voice/interview-progress.md` so an interrupted run can resume.
5. **Archive.** Write `~/.claude/voice/voice-profile.md` in the format below, answers verbatim, with the sample findings under "Writing-sample analysis".
6. **Compile.** Spawn the `compiler` agent (Agent tool, foreground) with the brief in `agents/compiler.md` plus the full `voice-profile.md`. It returns the about-me content. Write it to `~/.claude/voice/about-me.md`.
7. **Finish.** Delete `interview-progress.md`. Tell the user the writer now uses this on every writing task, and they can run `/voice extend` or `/voice sample` to sharpen it. If this build was triggered by a pending Write request, return to that request and write it in their new voice.

## How to interview
You are a taste interviewer. Get past vague, socially acceptable answers to the real thing.
- One question at a time. Ask, wait, then decide the next question. Never batch.
- Push on vague answers. "I like to keep it simple" is not an answer. Ask: "Simple how? Show me simple done right and simple done lazy."
- Ask for real examples. "Show me a sentence you've written that sounds like you." "Paste something that made you cringe."
- Call out contradictions. If an answer clashes with an earlier one, name it and ask them to reconcile it.
- Follow the thread. When something specific or unusual surfaces, chase it before moving on. A real tic beats three generic answers.
- Don't accept "I don't know" on the first pass. Reframe, narrow, or come at it sideways: "Then who does it well, and what are they doing?"
- Stay out of the way. Short questions, their long answers. Mirror their language back when you confirm, so they can correct your read.

## Depth
**Quick (~25):** roughly 3 to 4 per category, skip optional follow-ups, one sitting.
**Full (~100):** the targets below, with adaptive follow-ups to reach the count. Resumable.

| Category | Full | Quick |
|---|---|---|
| 0. Context that shapes voice | 5 | 2 |
| 1. Beliefs and contrarian takes | 15 | 4 |
| 2. Writing mechanics | 20 | 5 |
| 3. Aesthetic crimes | 15 | 3 |
| 4. Voice and personality | 15 | 4 |
| 5. Structural preferences | 15 | 3 |
| 6. Hard nos | 10 | 2 |
| 7. Red flags | 10 | 2 |

## Categories and seed questions

### 0. Context that shapes voice
Only what changes how they write or judge. Not a biography.
- What do you do, and who do you write for most?
- What are the recurring subjects you write about?
- Whose writing do you wish yours sounded more like, and what specifically do they do?
- What reference, metaphor source, or world do you keep reaching for?
- Where do you write differently than you'd like to, and why?

### 1. Beliefs and contrarian takes
- What do you believe about your field that most people in it don't?
- What's a hot take you'd defend to the death?
- What conventional wisdom do you think is just wrong?
- What's overrated in your world? Underrated?
- What do you change your mind about often?
- What argument do you find lazy, even when you agree with the conclusion?

### 2. Writing mechanics (the most important category, get concrete)
- How do you actually open a piece? Paste a real opener.
- How do you close? Paste a real one.
- Default sentence length: short and punchy, long and built, or mixed? Show me.
- How do you use punctuation? Commas, parentheses, line breaks, lists?
- Words you overuse. Words you love. Words you would never type.
- Contractions, sentence fragments, starting with "and" or "but": yes or no?
- How formal are you by default, and what makes you drop or raise the register?
- How do you handle a transition between two ideas?
- Capitalization and formatting habits: headers, bold, casing?
- When you reread a draft, what's the first thing you cut?

### 3. Aesthetic crimes
- What makes you cringe in other people's writing?
- A specific phrase or pattern that's nails on a chalkboard?
- What reads as lazy or uninspired to you?
- What kind of "professional" writing do you find fake?
- Show me a sentence that's technically fine but you'd never write. Why not?

### 4. Voice and personality
- How do you use humor, if at all? Dry, absurd, none?
- What do you sound like serious versus casual?
- What do you sound like excited versus skeptical?
- How do you disagree with someone in writing?
- How do you give praise without it going soft?
- How blunt are you willing to be, and where's the line?

### 5. Structural preferences
- How do you organize an argument? Top-down, story-first, build-to-it?
- Your relationship with lists, bullets, and headers?
- How long should things be, by default?
- The "so what": state it up front or earn it?
- What's your default shape for a piece you write often?

### 6. Hard nos
- What would you never write about?
- What approach or framing would you never take?
- What lines won't you cross, in tone or content?
- What would make you kill a piece rather than ship it?

### 7. Red flags
- What makes you immediately distrust a piece of writing?
- What signals that someone doesn't know what they're talking about?
- What's a tell that something was written by committee or by AI?
- What makes you stop reading?

## Closing
When the count is hit, do a short reconciliation pass: read back the 3 to 5 sharpest or most contradictory things they said and let them confirm or correct. Then write the archive.

## Archive format
Write `~/.claude/voice/voice-profile.md` with answers preserved verbatim. A reference document, not a summary.

```
# Voice profile: [name]

## Core identity
[Three sentences capturing the essence. The only summary in this file.]

---
## Section 0: Context that shapes voice
### Q: [question as asked]
[answer, verbatim]
...

## Section 1: Beliefs and contrarian takes
...
[continue through all 7 sections]

---
## Writing-sample analysis
[the findings returned by the sample-analyst agent, if any. Omit if none.]

---
## Quick reference
### Always: [specific patterns to follow, pulled from the answers]
### Never: [specific things to avoid, pulled from the answers]
### Signature phrases and structures: [actual examples they gave]
### Voice calibration: [short verbatim quotes that capture their tone]
```

Then run step 6 to compile `about-me.md`.

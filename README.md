<p align="center">
  <img src="assets/voice.svg" alt="voice" width="820">
</p>

<p align="center">
  <b>A Claude Code skill that learns how you write, then writes as you.</b><br>
  It strips the indicators that scream "an AI wrote this," and instead writes in <i>your</i> voice.
</p>

<p align="center">
  <img alt="Claude Code skill" src="https://img.shields.io/badge/Claude%20Code-skill-d97757">
  <img alt="python 3" src="https://img.shields.io/badge/python-3-3776ab?logo=python&logoColor=white">
  <img alt="em dashes: 0" src="https://img.shields.io/badge/em%20dashes-0-ff5c5c">
  <img alt="AI tells: stripped" src="https://img.shields.io/badge/AI%20tells-stripped-22c55e">
  <img alt="voice: yours" src="https://img.shields.io/badge/voice-yours-8b5cf6">
</p>

---

## Don't want your writing to sound like this slop?

> "a symphony of," "a tapestry of," "delicate balance"
>
> "It's not just a spreadsheet, it's a journey toward holistic, data-driven excellence."
>
> "Great question! Happy to help you delve into this robust, multifaceted tapestry."
>
> "At the end of the day, this isn't about features, it's about empowering stakeholders to thrive."
>
> "Furthermore, our best-in-class platform seamlessly elevates your workflow to the next level — because the future is now."
>
> "You didn’t just use them—you embodied them."

You have read a thousand of these: the cover letter, the LinkedIn posts, the em dash. I cannot stand these things. Every time I see a blog or an article with "it's not x, it's y" I lose my mind. Every time I see "the industry that is quietly taking over the world" I want to never read again. We have lost all prose in a sea of generic AI slop.


## The pitch

`voice` attempts to fix these issues in two ways. Building your voice profile with an interview, and by running a determinstic checker & adversarial model review to always attempt to remove AI tells, and match your true writing style. 

Simply run the skill, `/voice`, and it will begin to build your voice profile. 


## How it works

Three passes run on every draft, then a final deterministic gate & adversarial model review. (If you don't have codex cli or claude code cli, the adversarial review will just fail silently).

- **Strip AI tells** (`tells.md`, enforced by `check.py`): em dashes, validation filler, prefaces, inflated vocabulary, copula avoidance, significance inflation, formula patterns.
- **Apply craft** (`craft.md`): lead with the point, one idea per sentence, match length to the job, keep a pulse when it is meant to be read.
- **Write in your voice** (`about-me.md` + `learnings/`): the compiled profile of how you sound, plus every correction you have given. Tells are the floor, your voice is the layer on top.

The main rule behind all of it: every sentence must earn its place, by carrying information or doing work (a concrete image, rhythm, tension, a real opinion). 

## It learns from you twice

**Up front,** when you build it: an interview about how you think and write, plus analysis of writing samples you paste in.

**Continuously,** as you use it. When you say "I don't like how this is worded" or "too formal" or "never open like that," the skill captures the correction as a short note in `~/.claude/voice/learnings/` and reads it on every future write. 


## Quickstart

```bash
git clone https://github.com/lanmalkieri/voice ~/.claude/skills/voice

```

### :kiss: Or just point Claude Code to this repo and ask to set it up for you. :kiss:
### :kiss: Waste those tokens on trivial tasks! :kiss:


Start a new Claude Code session, then:

```text
/voice            build your voice (samples first, then an interview)
/voice quick      the ~25 question core
/voice sample     paste your writing (or a path) to learn from it
```

> [!TIP]
> Dictate the interview answers instead of typing them. Talking how you actually talk gives a truer voice profile than careful typing. [Wispr Flow](https://wisprflow.ai/) is a solid voice-to-text tool for it.

After that, any writing request comes out in your voice. Tell it "I don't like how this is worded" and the fix sticks.

## Commands

| Command | What it does |
|---|---|
| `/voice` | Build your voice: samples, interview, compile |
| `/voice quick` &middot; `/voice full` | ~25 vs ~100 question build |
| `/voice sample [text or paths]` | Analyze your writing, fold it into the profile |
| `/voice learn [note]` | Record a correction or preference by hand |
| `/voice view` | Print your compiled profile |
| `/voice extend` | More questions, append, recompile |
| `/voice recompile` | Rebuild the compact profile from the archive |
| `/voice refresh` | Back up, then rebuild from scratch |
| `/voice status` | What exists and when it was built |

Write, edit, and review requests route through the skill automatically. So does wording feedback: you rarely need `/voice learn` by hand, just say what you do not like.

## The gate (`check.py`)

Two layers run before any draft is finalized:

1. **Static checks**: banned characters, phrases, words, regex. Instant, free, always on.
2. **LLM judge**: a fast model catches AI tone the static list cannot. It runs on whatever you have, codex first, then the Claude Code CLI. Neither installed? It fails silently to static only.


<details>
<summary><b>Backend and toggle env vars</b></summary>

| Env var | Default | Meaning |
|---|---|---|
| `ANTI_AI_NO_LLM` | unset | `1` skips the LLM judge |
| `ANTI_AI_LLM_BACKEND` | `auto` | `auto` (codex then claude), `codex`, or `claude` |
| `ANTI_AI_LLM_TIMEOUT` | `60` | seconds before a backend call is abandoned |
| `ANTI_AI_CODEX_MODEL` | empty | model for `codex -m`. Empty omits `-m` (a forced model can 400 on a ChatGPT-account codex login) |
| `ANTI_AI_CLAUDE_MODEL` | `haiku` | model for `claude --model` |
| `ANTI_AI_CODEX_BIN`, `ANTI_AI_CLAUDE_BIN` | from PATH | override the binary path |
</details>

## Under the hood

```
SKILL.md            entry + routing (write / build / sample / learn / review / manage)
build.md            the builder: samples, interview, archive, compile
tells.md            the AI fingerprint to strip
craft.md            how to write well
check.py            the deterministic gate
agents/
  sample-analyst.md  reads your writing, returns style findings
  compiler.md        compiles the archive into the compact profile
  critic.md          judges a draft against your voice
```

Three small agents do the isolated jobs (analyze, compile, critique). The main session runs the interview, drafts, captures learnings, and writes the files.

Your profile and learnings live in `~/.claude/voice/` and are gitignored. This repo is the naked skill.

## Good to know

- By default the skill triggers on any writing task and builds a profile before its first write. Say "just write it" to skip the voice layer for a one-off, or edit the Write route in `SKILL.md`.
- The interview can span sessions. Progress saves to `~/.claude/voice/interview-progress.md` and resumes.
- Learnings are recent, specific overrides. When one conflicts with the profile, the learning wins. Fold durable ones into the profile with `/voice recompile`.

<p align="center">
  <img src="assets/banner.svg" alt="voice" width="820">
</p>

<p align="center">
  <b>A Claude Code skill that learns how you write, then writes as you.</b><br>
  It strips the tells that scream "an AI wrote this," applies real craft, and speaks in <i>your</i> voice.
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

> "In today's fast-paced world, let's dive in and unlock the full potential of synergy."
>
> "It's not just a spreadsheet, it's a journey toward holistic, data-driven excellence."
>
> "Great question! Happy to help you delve into this robust, multifaceted tapestry."
>
> "At the end of the day, this isn't about features, it's about empowering stakeholders to thrive."
>
> "Furthermore, our best-in-class platform seamlessly elevates your workflow to the next level — because the future is now."

Five sentences, zero humans. You have read a thousand of them: the cover letter, the LinkedIn post apologizing for existing, the chatbot clearing its throat for two paragraphs before it answers anything. The em dash. The rule of three. The "I hope this helps." `voice` deletes the genre.

## The pitch

Much like this README, most AI writing reads the same: smooth, padded, allergic to a real opinion. `voice` fixes that in two moves. It rips out the machine fingerprint, and it rebuilds your actual style from an interview, from your own writing, and from every correction you make along the way.

One command, `/voice`, builds your voice and writes in it.

> [!NOTE]
> This README keeps its own prose clean on purpose. The tool would flag the hype.

### See the difference

<table>
<tr><th>The model's voice</th><th>Yours</th></tr>
<tr><td>

> In today's fast-paced world, our robust platform leverages cutting-edge synergy to unlock seamless collaboration. It's not just software, it's a journey.

</td><td>

> A missed handoff never announces itself. The task sits in an inbox over the weekend, the deadline slips, and Monday morning two people each think the other had it.

</td></tr>
</table>

## How it works

Three passes on every draft, then a gate that refuses to ship slop.

```mermaid
flowchart LR
    A["you ask for writing"] --> B{"voice built?"}
    B -- no --> C["/voice build<br/>interview + your samples"]
    C --> D["draft in your voice"]
    B -- yes --> D
    D --> E["strip AI tells"]
    E --> F["apply craft"]
    F --> G{"check.py"}
    G -- FAIL --> D
    G -- PASS --> H["ship it"]
```

- **Strip AI tells** (`tells.md`, enforced by `check.py`): em dashes, validation filler, prefaces, inflated vocabulary, copula avoidance, significance inflation, formula patterns.
- **Apply craft** (`craft.md`): lead with the point, one idea per sentence, match length to the job, keep a pulse when it is meant to be read.
- **Write in your voice** (`about-me.md` + `learnings/`): the compiled profile of how you sound, plus every correction you have given. Tells are the floor, your voice is the layer on top.

The one rule behind all of it: every sentence must earn its place, by carrying information or doing real work (a concrete image, rhythm, tension, a real opinion). Everything else gets cut.

## It learns from you twice

**Up front,** when you build it: an interview about how you think and write, plus analysis of writing samples you paste in.

**Continuously,** as you use it. When you say "I don't like how this is worded" or "too formal" or "never open like that," the skill captures the correction as a short note in `~/.claude/voice/learnings/` and reads it on every future write. Your voice sharpens with use instead of drifting.

```mermaid
flowchart LR
    R["you react: 'don't word it like that'"] --> L["captured to learnings/"]
    L --> W["read on the next write"]
    W --> R
```

## Quickstart

```bash
git clone https://github.com/lanmalkieri/voice ~/.claude/skills/voice
```

Start a new Claude Code session, then:

```text
/voice            build your voice (samples first, then an interview)
/voice quick      the ~25 question core
/voice sample     paste your writing (or a path) to learn from it
```

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

Two layers run before any draft ships:

1. **Static checks**: banned characters, phrases, words, regex. Instant, free, always on.
2. **LLM judge**: a fast model catches AI tone the static list cannot. It runs on whatever you have, codex first, then the Claude Code CLI. Neither installed? It fails open to static only.

```mermaid
flowchart LR
    D["draft"] --> S["static checks"]
    S --> J{"LLM judge"}
    J --> X["codex"]
    X -- works --> V["PASS / FAIL"]
    X -- "missing or fails" --> Y["claude -p"]
    Y --> V
    J -. "neither installed" .-> Z["static-only<br/>(fail open)"]
```

Run it on anything:

```bash
printf '%s' "your text here" | python3 ~/.claude/skills/voice/check.py
# add --no-llm for static-only
```

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

Your profile and learnings live in `~/.claude/voice/` and are gitignored. This repo is the naked skill, ready to fork and make yours.

## Good to know

- By default the skill triggers on any writing task and builds a profile before its first write. Say "just write it" to skip the voice layer for a one-off, or edit the Write route in `SKILL.md`.
- The interview can span sessions. Progress saves to `~/.claude/voice/interview-progress.md` and resumes.
- Learnings are recent, specific overrides. When one conflicts with the profile, the learning wins. Fold durable ones into the profile with `/voice recompile`.

<p align="center"><sub>A Claude Code skill. Strip the tells. Keep the human.</sub></p>

# voice

A Claude Code skill that learns how you write, then writes in your voice. It does three things to every piece of writing: strips the tells that mark text as AI, applies a set of craft rules, and writes as you, from a voice profile built by interviewing you and analyzing your own writing. A deterministic Python gate (`check.py`) checks every draft before it ships.

One command, `/voice`, both builds your voice and uses it.

## How it works

Every draft gets three passes:

1. **Strip AI tells** (`tells.md`, enforced by `check.py`): em dashes, validation filler, prefaces, inflated vocabulary, copula avoidance, significance inflation, formula patterns, and more. The enforced list lives in `check.py`; `tells.md` is the concept behind it.
2. **Apply craft** (`craft.md`): lead with the point, one idea per sentence, match length to the job, keep a pulse when the writing is meant to be read.
3. **Write in your voice** (`~/.claude/voice/about-me.md`): the compiled profile of how you specifically sound. The tells are the floor; your voice is the layer on top.

The guiding rule: every sentence must earn its place, by carrying information or by doing real work (a concrete image, rhythm, tension, a real opinion). Everything else gets cut.

## Install

This is a user-level Claude Code skill. Clone it into your skills directory:

```bash
git clone https://github.com/lanmalkieri/voice ~/.claude/skills/voice
```

Start a new Claude Code session so it picks up the skill.

## Usage

Build your voice:

- `/voice` then follow the prompts. It asks for writing samples first, runs an interview about how you think and write, then compiles a compact profile.
- `/voice quick` runs a ~25 question core. `/voice full` runs the full ~100. The interview can span sessions and resumes where it stopped.

Feed it your writing:

- `/voice sample` then paste text, or `/voice sample ~/path/to/file.md` (files, a folder, or URLs). It analyzes your writing for rhythm, openers, favorite words, tics, and tells, and folds them into your profile. Works with or without an existing profile. With none, it bootstraps a voice from the writing alone, no interview required.

Write and review:

- Any drafting, editing, or rewriting request runs through the skill and comes out in your voice.
- "Does this sound like me" or "review this" runs a critic pass plus the gate and returns fixes.

Manage:

- `/voice view`, `/voice extend`, `/voice recompile`, `/voice refresh`, `/voice status`.

## The gate (`check.py`)

`check.py` is a deterministic check run on every draft before delivery. Two layers:

1. **Static checks** (instant, free): banned characters, phrases, words, and regex patterns. Always runs.
2. **LLM judge** (optional): sends the draft and the rubric to a fast model that catches AI tone the static list cannot. It runs on whichever CLI is installed, Codex first, falling back to the Claude Code CLI (`claude -p`). If neither is installed, the judge fails open and the static checks still enforce.

Run it directly:

```bash
printf '%s' "your text here" | python3 ~/.claude/skills/voice/check.py
```

Add `--no-llm` to skip the LLM judge and run static checks only.

### Backends and toggles

| Env var | Default | Meaning |
|---|---|---|
| `ANTI_AI_NO_LLM` | unset | `1` skips the LLM judge |
| `ANTI_AI_LLM_BACKEND` | `auto` | `auto` (codex then claude), `codex`, or `claude` |
| `ANTI_AI_LLM_TIMEOUT` | `60` | seconds before a backend call is abandoned |
| `ANTI_AI_CODEX_MODEL` | empty | model for `codex -m`. Empty omits `-m` so codex uses its account default. A forced model can 400 on a ChatGPT-account codex login |
| `ANTI_AI_CLAUDE_MODEL` | `haiku` | model for `claude --model` |
| `ANTI_AI_CODEX_BIN`, `ANTI_AI_CLAUDE_BIN` | from PATH | override the binary path |

Requirements: Python 3. For the LLM judge, at least one of the Codex CLI or the Claude Code CLI. Without either, the gate runs static only.

## Files

```
SKILL.md              entry point and routing (write / build / review / sample / manage)
build.md              the builder: samples, interview, archive, compile
tells.md              the AI fingerprint to strip
craft.md              how to write well
check.py              the deterministic gate
agents/
  sample-analyst.md   analyzes your writing samples
  compiler.md         compiles the archive into the compact profile
  critic.md           judges a draft against your voice
```

Your generated profile is not in this repo. The interview answers, sample analysis, and compiled profile are written to `~/.claude/voice/` and are gitignored. This repo is the naked skill only.

## Behavior notes

- By default the skill triggers on any writing task and, if you have not built a profile yet, builds one before writing. To skip that for a one-off, say "skip voice" or "just write it" and it drafts with the tells and craft only. To change the default, edit the Write route in `SKILL.md`.
- The agents analyze and judge only. The main session runs the interview, drafts, and writes every file.

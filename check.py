#!/usr/bin/env python3
"""Anti-AI-writing gate.

Two layers:
  1. Static checks (instant, free): banned characters, phrases, words, regex
     patterns. The floor. Always runs.
  2. LLM judge (optional): the draft and the rubric go to a cheap/fast model that
     returns a JSON verdict catching AI-tone moves the static list cannot. The
     judge runs on whichever backend is available: the Codex CLI first, and if
     codex is not installed it falls back to the Claude Code CLI (claude -p).

The LLM layer fails open: if no backend is installed, the judge is disabled, the
call times out, or the output is unparseable, the static checks still enforce and
the gate prints a note instead of blocking on the judge. In auto mode a per-call
failure on one backend falls through to the next.

This gate has no registers. One rubric judges every kind of writing: it fails AI
tells everywhere, but it does NOT require a fact in every sentence, so prose with
rhythm, imagery, and opinion passes.

Toggles (env):
  ANTI_AI_NO_LLM=1        skip the LLM judge
  ANTI_AI_LLM_BACKEND     auto (default), codex, or claude. auto tries codex then
                          claude. codex/claude force that one backend only.
  ANTI_AI_LLM_TIMEOUT     seconds before a backend call is abandoned (default 60).
                          ANTI_AI_CODEX_TIMEOUT is still honored for back-compat.
  ANTI_AI_CODEX_MODEL     model passed to codex -m. Default empty: -m is omitted
                          so codex uses its account-default model. A forced model
                          can 400 on a ChatGPT-account codex login.
  ANTI_AI_CLAUDE_MODEL    model passed to claude --model (default: haiku)
  ANTI_AI_CODEX_BIN       override the codex binary path (for testing)
  ANTI_AI_CLAUDE_BIN      override the claude binary path (for testing)
CLI:
  --no-llm                same as ANTI_AI_NO_LLM=1
"""
import json
import os
import re
import shutil
import subprocess
import sys

BANNED_CHARS = ["—", "–"]

BANNED_PHRASES = [
    # validation / sycophancy
    "that's real",
    "you're valid",
    "that's valid",
    "your frustration is valid",
    "i hear you",
    "i see you",
    "i completely understand",
    "i totally understand",
    "you're not wrong",
    "you're not crazy",
    "that makes sense",
    "it makes sense that",
    "you're absolutely right",
    "i hope this helps",
    "i hope this is helpful",
    "i appreciate you sharing",
    "thank you for sharing",
    # prefaces / signposting
    "great question",
    "good question",
    "excellent question",
    "important question",
    "absolutely",
    "certainly",
    "happy to help",
    "let's dive in",
    "let's break it down",
    "let's unpack",
    "here's what you need to know",
    "without further ado",
    "let me walk you through",
    "in today's world",
    "in today's fast-paced world",
    "in the ever-evolving landscape",
    "in the realm of",
    "when it comes to",
    "imagine a world",
    # transition filler
    "at the end of the day",
    "the bottom line is",
    "the key takeaway is",
    "it is worth noting",
    "it's worth noting",
    "it is important to note",
    "it's important to note",
    "keep in mind",
    "bear in mind",
    "in summary",
    "in conclusion",
    "to summarize",
    "to conclude",
    "as previously mentioned",
    "this is not an exhaustive list",
    # persuasive-authority tropes
    "the real question is",
    "at its core",
    "what really matters",
    "the heart of the matter",
    "make no mistake",
    "the truth is",
    "the reality is",
    # copula avoidance
    "serves as a",
    "serves as an",
    "stands as a",
    "stands as an",
    # significance / legacy inflation
    "a testament to",
    "marks a pivotal moment",
    "leaves an indelible mark",
    "leaving an indelible mark",
    "underscores its importance",
    # weasel attributions
    "experts argue",
    "experts say",
    "experts believe",
    "observers note",
    "critics argue",
    "industry reports",
    "it is widely believed",
    # speculative gap-filling
    "maintains a low profile",
    "as of my last update",
    "as of my last training",
    "as of my knowledge cutoff",
    # filler / hedging
    "due to the fact that",
    "at this point in time",
    "has the ability to",
]

BANNED_WORDS = [
    "delve", "tapestry", "realm", "landscape", "ecosystem", "synergy",
    "paradigm", "journey", "robust", "seamless", "pivotal", "crucial",
    "vital", "essential", "transformative", "groundbreaking", "cutting-edge",
    "innovative", "dynamic", "comprehensive", "holistic", "nuanced",
    "multifaceted", "intricate", "interplay", "meticulous", "meaningful",
    "impactful", "scalable", "actionable", "strategic", "tailored", "bespoke",
    "game-changing", "unprecedented", "unparalleled", "vibrant", "profound",
    "elevate", "unlock", "unleash", "harness", "leverage", "utilize",
    "facilitate", "empower", "streamline", "optimize", "maximize",
    "revolutionize", "navigate", "embark", "unpack", "illuminate",
    "underscore", "showcase", "foster", "cultivate", "spearhead",
    "enhance", "amplify", "resonate", "align", "bolster", "garner",
    "poised", "testament", "beacon", "cornerstone", "symphony",
    "catalyst", "crucible", "flywheel", "north star", "renowned",
    "nestled", "boasts", "breathtaking",
]

BANNED_REGEX = [
    r"\bnot only\b.+\bbut also\b",
    r"\bnot just\b.+\bbut\b",
    r"\bnot merely\b.+\bbut\b",
    r"\bthis (is|isn't|is not) .+\b(this is|it's|it is)\b",
    r"\bit (isn't|is not) .+\b(it is|it's)\b",
    r"\bless .+,\s*more .+\b",
    r"\bforget .+\.\s*focus on .+\b",
    r"\bstop thinking .+\.\s*start thinking .+\b",
    r"\b.+ is dead\.\s*.+ is the future\b",
    r"\bthe (question|issue|problem|answer|goal) is not .+\b",
    r"\bit was never about .+\.\s*it was always about .+\b",
    r"\bfrom .+ to .+,\s*.+\b",
    r"\bmore than .+,\s*.+\b",
    r"\bbeyond .+,\s*.+\b",
    # superficial -ing tail: comma + present participle that fakes depth
    r",\s+(highlighting|underscoring|emphasizing|reflecting|symbolizing|"
    r"showcasing|fostering|cultivating|reinforcing|demonstrating|signaling|"
    r"cementing|solidifying)\b",
]

JUDGE_RUBRIC = """You are a strict editor enforcing anti-AI-writing rules.

The rule behind every ban: every sentence must earn its place. It earns it by
carrying information (a fact, a number, a decision, evidence, a next action), OR,
in writing meant to be read for its own sake, by doing real work: moving the
piece forward, building a concrete image, setting rhythm, or landing a real
opinion. Do NOT fail a sentence merely because it lacks a number or a fact.
Varied and longer sentences, a scene-first opening, concrete sensory imagery, a
genuine opinion, and an earned three-beat cadence are all good, not violations.
The enemy is generic machine prose, not personality or beauty.

FAIL these, always, in any kind of writing:
- Validation or affirmation that carries no work: "that's real", "I hear you",
  "you're not wrong", "you're absolutely right", "I hope this helps".
- AI prefaces and signposting: "Great question", "Absolutely", "Happy to help",
  "Let me", "Here is", "Let's dive in", "Here's what you need to know",
  "Imagine a world", "In today's...", "Without further ado".
- Transition filler: Furthermore, Moreover, However, Ultimately, Overall,
  In conclusion, In summary, "It is worth noting", "It is important to note".
- Inflated vocabulary standing in for a concrete idea: robust, seamless,
  leverage, streamline, comprehensive, holistic, strategic, vibrant, tapestry,
  ecosystem, journey, unlock, empower, elevate, foster.
- Copula avoidance: "serves as", "stands as", "boasts", "represents a",
  "features" where "is", "are", or "has" is meant.
- Significance inflation: "stands as a testament", "marks a pivotal moment",
  "underscores its importance", "reflects a broader shift".
- Superficial -ing tails that fake depth: "..., highlighting the deep
  connection", "..., underscoring its significance".
- Weasel attributions with no named source: "experts argue", "observers note",
  "industry reports suggest".
- Persuasive-authority tropes: "the real question is", "at its core",
  "what really matters", "the heart of the matter".
- Speculative gap-filling dressed as fact: "likely grew up", "maintains a low
  profile", "as of my last update".
- "not X, but Y" and tagline formulas ("X reimagined", "X made simple"),
  false ranges, and rule-of-three reflexes.
- Em or en dashes; mechanical mid-sentence boldface; Title Case headings;
  decorative emoji.
- Any sentence that is only decoration with no work behind it.

Do not flag a plain greeting line or a plain sign-off. Do not flag a concrete
fact, number, decision, or next step even when it is friendly."""

JUDGE_INSTRUCTION = (
    'Return ONLY a single JSON object, no prose, in this exact shape: '
    '{"verdict":"PASS" or "FAIL","violations":'
    '[{"quote":"the offending text","rule":"which rule","fix":"a concrete rewrite"}]}. '
    "If the draft is clean, return verdict PASS with an empty violations list."
)


def find_static_violations(text):
    violations = []
    lower = text.lower()
    for char in BANNED_CHARS:
        if char in text:
            violations.append(f"banned character: {char}")
    for phrase in BANNED_PHRASES:
        if phrase in lower:
            violations.append(f"banned phrase: {phrase}")
    for word in BANNED_WORDS:
        if re.search(rf"\b{re.escape(word)}\b", lower):
            violations.append(f"banned word: {word}")
    for pattern in BANNED_REGEX:
        if re.search(pattern, lower, flags=re.DOTALL):
            violations.append(f"banned pattern: {pattern}")
    return sorted(set(violations))


def _extract_last_json(s):
    spans = []
    depth = 0
    start = None
    for i, ch in enumerate(s):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}" and depth > 0:
            depth -= 1
            if depth == 0 and start is not None:
                spans.append(s[start:i + 1])
                start = None
    for cand in reversed(spans):
        try:
            return json.loads(cand)
        except json.JSONDecodeError:
            continue
    return None


def _judge_timeout():
    return int(
        os.environ.get(
            "ANTI_AI_LLM_TIMEOUT", os.environ.get("ANTI_AI_CODEX_TIMEOUT", "60")
        )
    )


def _codex_cmd(codex, prompt):
    # Omit -m unless explicitly set. A forced model (e.g. gpt-5-mini) 400s on a
    # ChatGPT-account codex login; with no -m, codex uses its working account
    # default. -c overrides reasoning effort to low for speed regardless.
    model = os.environ.get("ANTI_AI_CODEX_MODEL", "")
    cmd = [codex, "exec"]
    if model:
        cmd += ["-m", model]
    cmd += [
        "-c", 'model_reasoning_effort="low"',
        "--skip-git-repo-check",
        "--sandbox", "read-only",
        prompt,
    ]
    return cmd


def _claude_cmd(claude_bin, prompt):
    model = os.environ.get("ANTI_AI_CLAUDE_MODEL", "haiku")
    return [
        claude_bin, "-p", prompt,
        "--model", model,
        "--output-format", "text",
    ]


def _run_backend(name, binpath, prompt, timeout):
    """Run one backend. Return (obj, None) on success or (None, error_str)."""
    cmd = _codex_cmd(binpath, prompt) if name == "codex" else _claude_cmd(binpath, prompt)
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None, f"{name} timed out after {timeout}s"
    except OSError as exc:
        return None, f"{name} call failed: {exc}"
    obj = _extract_last_json(proc.stdout)
    if obj is None:
        return None, f"{name} returned unparseable output"
    obj["_backend"] = name
    return obj, None


def llm_judge(text):
    """Return a dict from the LLM judge, or None if the judge did not run.

    Backend order is set by ANTI_AI_LLM_BACKEND: auto (codex then claude),
    codex (codex only), or claude (claude only). A backend with no binary, or
    that fails, is skipped; in auto mode the next backend is tried.
    """
    if os.environ.get("ANTI_AI_NO_LLM") == "1" or "--no-llm" in sys.argv:
        return None
    backend = os.environ.get("ANTI_AI_LLM_BACKEND", "auto").lower()
    if backend not in ("auto", "codex", "claude"):
        backend = "auto"
    codex = os.environ.get("ANTI_AI_CODEX_BIN") or shutil.which("codex")
    claude_bin = os.environ.get("ANTI_AI_CLAUDE_BIN") or shutil.which("claude")

    if backend == "codex":
        order = [("codex", codex)]
    elif backend == "claude":
        order = [("claude", claude_bin)]
    else:
        order = [("codex", codex), ("claude", claude_bin)]

    prompt = (
        JUDGE_RUBRIC
        + "\n\nDRAFT TO JUDGE:\n<<<\n"
        + text
        + "\n>>>\n\n"
        + JUDGE_INSTRUCTION
    )
    timeout = _judge_timeout()
    tried = []
    for name, binpath in order:
        if not binpath:
            tried.append(f"{name} not found")
            continue
        obj, err = _run_backend(name, binpath, prompt, timeout)
        if obj is not None:
            return obj
        tried.append(err)
    return {"error": "; ".join(tried) if tried else "no llm backend found"}


def main():
    text = sys.stdin.read()
    static = find_static_violations(text)
    judge = llm_judge(text)

    llm_violations = []
    llm_note = None
    if judge is None:
        llm_note = "llm judge: skipped"
    elif "error" in judge:
        llm_note = f"llm judge: unavailable ({judge['error']}), static checks only"
    else:
        backend = judge.get("_backend", "?")
        verdict = str(judge.get("verdict", "")).upper()
        if verdict == "FAIL":
            for v in judge.get("violations", []):
                quote = v.get("quote", "").strip()
                rule = v.get("rule", "").strip()
                fix = v.get("fix", "").strip()
                line = f"llm: {quote}".rstrip()
                if rule:
                    line += f"  [{rule}]"
                if fix:
                    line += f"  -> {fix}"
                llm_violations.append(line)
            if not llm_violations:
                llm_violations.append("llm: FAIL (no detail returned)")
            llm_note = f"llm judge: FAIL (via {backend})"
        else:
            llm_note = f"llm judge: PASS (via {backend})"

    failed = bool(static) or bool(llm_violations)
    print("FAIL" if failed else "PASS")
    for v in static:
        print(f"- {v}")
    for v in llm_violations:
        print(f"- {v}")
    if llm_note:
        print(f"# {llm_note}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

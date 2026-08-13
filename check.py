#!/usr/bin/env python3
"""Anti-AI-writing gate.

Two layers:
  1. Static checks (instant, free): banned characters, phrases, words, regex
     patterns. The floor. Always runs.
  2. LLM judge (optional): the draft and the rubric go to a cheap/fast model that
     returns a JSON verdict. The judge is a LINTER: every violation must cite a
     rule verbatim from tells.md, about-me.md, or a learning, and violations
     citing rules that do not exist in those files are dropped by this script.
     Backend: the Codex CLI at low reasoning effort (~11s per lint), falling
     back to the Claude Code CLI (haiku) — claude -p carries ~100s of CLI
     harness overhead regardless of model, so it is fallback only.

The LLM layer fails open: if no backend is installed, the judge is disabled, the
call times out, or the output is unparseable, the static checks still enforce and
the gate prints a note instead of blocking on the judge. In auto mode a per-call
failure on one backend falls through to the next.

This gate has no registers. One rubric judges every kind of writing: it fails AI
tells everywhere, but it does NOT require a fact in every sentence, so prose with
rhythm, imagery, and opinion passes.

Toggles (env):
  ANTI_AI_NO_LLM=1        skip the LLM judge
  ANTI_AI_LLM_BACKEND     auto (default), codex, or claude. auto tries codex
                          (low effort) then claude. codex/claude force one.
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
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time

BANNED_CHARS = ["—", "–", "“", "”"]

BANNED_PHRASES = [
    # announcer phrases: frame information instead of delivering it. Delete the
    # frame and state the thing.
    "worth flagging",
    "worth noting",
    "worth calling out",
    "worth mentioning",
    "one thing to be aware of",
    "a few things to keep in mind",
    "things to keep in mind",
    "things to think through",
    "some open questions",
    "a couple of considerations",
    "a few considerations",
    # meta-narration about my own work / self-deprecation. The reader needs the
    # result, not the history of how it got that way.
    "instead of me",
    "rather than me",
    "hand-waving",
    "handwaving",
    "i should have caught",
    "i should have flagged",
    "good catch",
    "my bad",
    "as i mentioned earlier",
    # validation / sycophancy
    "take it for granted",
    "real movement",
    "i appreciate the movement",
    "that's a step in the right direction",
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
    "in today's fast-paced",
    "in the ever-evolving landscape",
    "in the dynamic world of",
    "in the dynamic landscape of",
    "in the world of",
    "as the world continues to evolve",
    "continues to evolve",
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
    "moving forward",
    "generally speaking",
    "cannot be overstated",
    "can't help but feel",
    "it's important to consider",
    "it is important to consider",
    "key takeaways",
    "deep dive",
    "let's dissect",
    "no fluff",
    "looming challenges",
    "shouting into the void",
    # forced sass / hot-take openers
    "but here's the thing",
    "here's the thing",
    "but here's the truth",
    "here's the truth",
    "here's what nobody",
    "what nobody's saying",
    "what nobody is saying",
    "then i realized",
    "hot take",
    "unpopular opinion",
    "let that sink in",
    "the result?",
    "what changed?",
    "the kicker",
    # universal authority without a source
    "studies show",
    "studies suggest",
    "research shows",
    "research suggests",
    "it's no secret",
    "it is no secret",
    "it's well known",
    "it is well known",
    # fluff adverbials and stage directions
    "with practiced efficiency",
    "with measured steps",
    "mastered precision",
    "surgical precision",
    "this is surgical",
    # stock metaphor / phrasing
    "delicate balance",
    "game changer",
    "gamechanger",
    # model self-disclosure
    "as a large language model",
    "as a large-scale language model",
    "as an ai language model",
    "i'm just an ai",
]

BANNED_WORDS = [
    # Reaction adverbs: narrate a feeling the writer cannot verify anyone had.
    # See learnings/2026-08-04-no-invented-expectations-or-reactions.md
    "surprisingly", "interestingly", "unsurprisingly",
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
    # transition filler (single words)
    "furthermore", "moreover", "additionally", "however", "therefore",
    "thus", "hence", "consequently", "nevertheless", "nonetheless",
    "notably", "importantly", "albeit", "indeed", "conversely",
    "likewise", "similarly", "game-changer",
]

BANNED_REGEX = [
    # Narrating adverbs bolted onto a verb: pure AI drama, zero information.
    # See learnings/2026-08-02-no-quietly-adverb-narration.md
    r"\b(quietly|steadily|gradually|inevitably|invariably)\s+\w+",
    # Invented expectations / reactions: asserting an internal state nobody stated.
    # Unverifiable by construction, so it is fabrication.
    # See learnings/2026-08-04-no-invented-expectations-or-reactions.md
    r"\bthan (we|I|you|anyone|they) (expected|thought|assumed|anticipated)\b",
    r"\b(we|I|you|they) (had )?(expected|assumed|anticipated) (that|it|this)\b",
    r"\bas you('d| would| might)? (expect|know|imagine)\b",
    r"\byou (may|might) have noticed\b",
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
    # false-range DOUBLING only ("from X to Y, from A to B"). The old
    # "from .+ to .+," was unbounded and, under the former DOTALL whole-document
    # search, failed any draft with "from" plus a later "to" and comma even in
    # unrelated paragraphs. A real range ("from 10 to 40 facilities,") is not a
    # tell. "more than .+," and "beyond .+," were dropped for the same reason:
    # high false-positive, not grounded in tells.md.
    r"\bfrom [^,.\n]+ to [^,.\n]+,\s*from [^,.\n]+ to\b",
    # superficial -ing tail: comma + present participle that fakes depth
    r",\s+(highlighting|underscoring|emphasizing|reflecting|symbolizing|"
    r"showcasing|fostering|cultivating|reinforcing|demonstrating|signaling|"
    r"cementing|solidifying)\b",
    # contrastive / inspirational pivot, with or without "but"
    r"\b(isn't|is not|not) just\b.{1,80}?\b(it'?s|it is|they'?re|they are)\b",
    # triad negation: "No X. No Y. Just Z." / "Not for X. Not for Y. For Z."
    r"\bno [^.\n]+\.\s*no [^.\n]+\.\s*just\b",
    r"\bnot for [^.\n]+\.\s*not for [^.\n]+\.\s*for\b",
    # listicle / title formulas
    r"\b\d+ things (you|to|i|we|that|every)\b",
    r"\bmaster .+ in \d+ (days|weeks|minutes|steps)\b",
    r"\bfrom [^,.\n]+ to [^,.\n]+:",
    # repeated exclamation marks for fake drama
    r"!{2,}",
]

# Emoji of any kind: decorative tone markers like the ones AI sprinkles in.
EMOJI_RE = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000026FF\U00002700-\U000027BF"
    "\U0001F1E6-\U0001F1FF\U00002B00-\U00002BFF\U0000FE0F]"
)

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
- Contrastive framing and inspirational pivots: "X isn't just A, it's B",
  "this isn't about A, it's about B" (specific to abstract, fake profundity).
- Asked-and-answered rhetorical questions: "What changed? The math did.",
  "Why? Because ...". State the answer instead.
- Triplet cadence used for glib authority: "fast, cheap, and out of control".
- Forced sass and hot-take openers: "but here's the thing", "here's what
  nobody is saying", "hot take", "let that sink in".
- Universal authority with no source ("studies show that...", "research
  proves"), and quotes with no real attribution.
- Forced or unmotivated similes, especially one per sentence.
- Double-assertion closers: a sentence that restates the previous one in vaguer
  or grander terms ("..., so your X improves instead of Y"). Stop after the
  concrete point.
- Em or en dashes; smart/curly quotes; mechanical mid-sentence boldface;
  Title Case headings; decorative emoji; repeated exclamation marks for drama.
- Any sentence that is only decoration with no work behind it.

Do not flag a plain greeting line or a plain sign-off. Do not flag a concrete
fact, number, decision, or next step even when it is friendly."""

JUDGE_INSTRUCTION = (
    'Return ONLY a single JSON object, no prose, in this exact shape: '
    '{"verdict":"PASS" or "FAIL","violations":'
    '[{"quote":"the offending text","rule":"which rule","fix":"a concrete rewrite"}]}. '
    "If the draft is clean, return verdict PASS with an empty violations list."
)

VOICE_DIR = os.environ.get("ANTI_AI_VOICE_DIR", os.path.expanduser("~/.claude/voice"))
SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
ABOUT_PATH = os.environ.get("ANTI_AI_ABOUT", os.path.join(VOICE_DIR, "about-me.md"))
LEARNINGS_DIR = os.environ.get("ANTI_AI_LEARNINGS", os.path.join(VOICE_DIR, "learnings"))
TELLS_PATH = os.environ.get("ANTI_AI_TELLS", os.path.join(SKILL_DIR, "tells.md"))
RECEIPTS_DIR = os.environ.get("ANTI_AI_RECEIPTS_DIR", os.path.join(VOICE_DIR, "receipts"))
RECEIPT_TTL = 24 * 3600  # receipts older than this are pruned on each write

VOICE_JUDGE_RUBRIC = """You are a style LINTER, not an editor. Your job is mechanical: check the draft against an explicit rulebook and report only violations of rules in that rulebook. You are not judging quality. Do not improve, tighten, or re-taste the writing. A draft that violates no rule is a PASS even if you could write it better. You do not have to find anything; most clean drafts PASS.

THE RULEBOOK, in increasing authority:
1. THE FLOOR (tells.md): universal AI tells.
2. THEIR VOICE (about-me.md): this author's own laws. A law here makes a pattern LEGAL for them even if it looks like a tell to you (flat imperatives, colon-led label lines, comma splices, lowercase names, EG/eg).
3. THEIR LEARNINGS: dated corrections, highest authority. Apply each learning ONLY to what its text literally states. Never generalize a learning to nearby cases. When unsure whether a learning applies, it does not apply.

A violation exists ONLY when you can point at the specific rule the quoted text breaks. In each violation's "rule" field, cite the rule by quoting it VERBATIM from the rulebook, prefixed with its source tag:
  floor: <verbatim text copied from tells.md>
  law: <verbatim text copied from about-me.md>
  learning:<file name>: <verbatim text copied from that learning>
A violation whose rule you cannot quote verbatim from the rulebook does not exist. Do not report it. Invented rules are discarded by the harness and waste the run.

Never flag:
- anything an about-me.md law or the allowlist endorses,
- sentence shapes and mechanics: imperatives, fragments, comma splices, long comma-chained sentences, casing and capitalization choices, product-name spellings,
- content, facts, structure, tone, or wording you merely find awkward. Awkward is not a rule,
- a rule you remember from somewhere else. If it is not in the rulebook below, it does not exist.

Return PASS with an empty violations list unless a named rule is broken."""


def _read_file(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read().strip()
    except OSError:
        return ""


def _laws_only(about):
    """The judge lints against rules, so it gets the rule-bearing sections of
    about-me.md (usage + laws), not the whole profile — the full profile more
    than doubles the prompt and slows every lint. The verbatim-rule validator
    still checks quotes against the FULL profile text."""
    sections = re.findall(
        r"<(usage|writing_laws|communication_laws)>.*?</\1>", about, re.DOTALL
    )
    if not sections:
        return about
    return "\n\n".join(
        m.group(0)
        for m in re.finditer(
            r"<(usage|writing_laws|communication_laws)>.*?</\1>", about, re.DOTALL
        )
    )


def load_voice_context():
    """Load the author's voice so the judge checks "does this sound like THEM",
    not just "is this generic AI slop". Returns None when no profile exists, in
    which case the judge falls back to the generic rubric (so the tool still
    works for someone who has not built a voice yet)."""
    about = _read_file(ABOUT_PATH)
    if not about:
        return None
    learnings = []
    try:
        for name in sorted(os.listdir(LEARNINGS_DIR)):
            if name.endswith(".md"):
                body = _read_file(os.path.join(LEARNINGS_DIR, name))
                if body:
                    learnings.append(f"## {name}\n{body}")
    except OSError:
        pass
    return {
        "about": about,
        "tells": _read_file(TELLS_PATH),
        "learnings": "\n\n".join(learnings),
    }


def find_static_violations(text, allowlist=None):
    allowlist = allowlist or set()
    violations = []
    lower = text.lower()
    lines = lower.splitlines() or [lower]
    for char in BANNED_CHARS:
        if char in text:
            violations.append(f"banned character: {char}")
    for phrase in BANNED_PHRASES:
        if phrase in allowlist:
            continue
        if phrase in lower:
            violations.append(f"banned phrase: {phrase}")
    for word in BANNED_WORDS:
        if word in allowlist:
            continue
        if re.search(rf"\b{re.escape(word)}\b", lower):
            violations.append(f"banned word: {word}")
    for pattern in BANNED_REGEX:
        # Match per line, never across the whole document. The old DOTALL search
        # over the full text let an unbounded .+ span unrelated paragraphs, so a
        # "from" in one paragraph plus a "to" and comma in another failed clean
        # writing. A paragraph is one line, so within-paragraph formulas still
        # get caught.
        if any(re.search(pattern, line) for line in lines):
            violations.append(f"banned pattern: {pattern}")
    for ch in sorted(set(EMOJI_RE.findall(text))):
        violations.append(f"banned emoji: {ch}")
    return sorted(set(violations))


ALLOWLIST_PATH = os.environ.get(
    "ANTI_AI_ALLOWLIST", os.path.expanduser("~/.claude/voice/allowlist.txt")
)


def load_allowlist():
    """Author-approved words and phrases to exempt from the static bans and the
    judge. One term per line in ~/.claude/voice/allowlist.txt, lowercased on
    load; blank lines and lines starting with # are ignored. This lets a real
    person's vocabulary ("scalable") and signature phrases ("in summary")
    survive the floor. Patterns are not allowlistable: fix the regex instead.
    """
    terms = set()
    try:
        with open(ALLOWLIST_PATH, encoding="utf-8") as fh:
            for raw in fh:
                term = raw.split("#", 1)[0].strip().lower()
                if term:
                    terms.add(term)
    except OSError:
        pass
    return terms


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
        # A bare `claude -p` boots the user's full config including MCP
        # servers, which alone blows past the 60s judge timeout. An empty
        # strict MCP config makes startup ~10s total on haiku.
        "--strict-mcp-config",
        "--mcp-config", '{"mcpServers":{}}',
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


def llm_judge(text, allowlist=None, ctx=None, changed_lines=None):
    """Return a dict from the LLM judge, or None if the judge did not run.

    Backend order is set by ANTI_AI_LLM_BACKEND: auto (claude/haiku then
    codex), codex (codex only), or claude (claude only). A backend with no
    binary, or that fails, is skipped; in auto mode the next backend is tried.

    `changed_lines`, when given, puts the judge in revision mode: unchanged
    lines from the previously linted draft are settled and out of scope.
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
        # codex at low reasoning effort: ~11s per lint with the trimmed
        # rulebook prompt. claude -p (any model, incl haiku) costs ~100s in
        # CLI harness overhead alone, so it is the fallback, not the default.
        order = [("codex", codex), ("claude", claude_bin)]

    allow_note = ""
    if allowlist:
        allow_note = (
            "\n\nThe author legitimately uses these words and phrases. Do NOT "
            "flag them as tells: " + ", ".join(sorted(allowlist)) + "."
        )
    if ctx is None:
        ctx = load_voice_context()
    if ctx:
        rubric = VOICE_JUDGE_RUBRIC
        refs = "\n\n=== THE FLOOR (tells.md) ===\n" + ctx["tells"]
        refs += "\n\n=== THEIR VOICE (about-me.md, laws) ===\n" + _laws_only(
            ctx["about"]
        )
        if ctx["learnings"]:
            refs += (
                "\n\n=== THEIR LEARNINGS (these override everything above) ===\n"
                + ctx["learnings"]
            )
    else:
        rubric = JUDGE_RUBRIC
        refs = ""
    revision_note = ""
    if changed_lines:
        revision_note = (
            "\n\nREVISION MODE: this draft is a revision of one you already "
            "linted. Every unchanged line is settled: do not flag it. Only "
            "these new or changed lines are in scope:\n"
            + "\n".join(f"> {line}" for line in changed_lines)
        )
    prompt = (
        rubric
        + refs
        + allow_note
        + revision_note
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


def _norm(text):
    # CRLF->LF, strip. voice-gate.py and the outbound guard use the SAME
    # normalization so a receipt matches the sent body despite line-ending or
    # trailing-newline drift between the gated draft and the outbound payload.
    return text.replace("\r\n", "\n").replace("\r", "\n").strip()


def _norm_ws(s):
    return re.sub(r"\s+", " ", s or "").strip().lower()


def _norm_rule(s):
    # For rule-quote validation only: judges reassemble markdown (heading +
    # body joined with ": ", "- " prefixes), so match on letters/digits alone.
    # Whitespace becomes a space FIRST, so punctuation removal cannot glue
    # words across line breaks ("sentences\nA" must not become "sentencesa").
    flat = re.sub(r"\s+", " ", (s or "").lower())
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", "", flat)).strip()


def validate_llm_violations(violations, ctx):
    """Enforce the linter contract mechanically: keep only violations whose
    "rule" field quotes a rule that actually exists in the rulebook, tagged
    floor:/law:/learning:<file>:. Everything else is an invented rule and is
    dropped. Returns (kept, dropped)."""
    kept, dropped = [], []
    floor_ref = _norm_rule(ctx.get("tells", "")) if ctx else ""
    law_ref = _norm_rule(ctx.get("about", "")) if ctx else ""
    for v in violations:
        rule = (v.get("rule") or "").strip()
        m = re.match(r"^(floor|law|learning)\s*:\s*(.*)$", rule, re.IGNORECASE | re.DOTALL)
        ok = False
        if m:
            tag, body = m.group(1).lower(), m.group(2).strip()
            if tag == "learning":
                m2 = re.match(r"^([^:]+?\.md)\s*:\s*(.*)$", body, re.DOTALL)
                if m2:
                    ref = _norm_rule(
                        _read_file(os.path.join(LEARNINGS_DIR, m2.group(1).strip()))
                    )
                    quoted = _norm_rule(m2.group(2))
                    ok = len(quoted) >= 15 and quoted[:40] in ref
            else:
                quoted = _norm_rule(body)
                ref = floor_ref if tag == "floor" else law_ref
                ok = len(quoted) >= 15 and quoted[:40] in ref
        (kept if ok else dropped).append(v)
    return kept, dropped


def _lint_state_path():
    sid = os.environ.get("CLAUDE_CODE_SESSION_ID")
    if not sid:
        return None
    return os.path.join(VOICE_DIR, "sessions", sid, "lint-state.json")


def load_lint_state():
    path = _lint_state_path()
    if not path:
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return None


def save_lint_state(text_n, llm_note, llm_violations):
    """Persist the llm outcome for this session's draft so re-runs converge:
    an identical draft reuses the verdict, an edited draft is judged only on
    its changed lines. Static checks always re-run in full."""
    path = _lint_state_path()
    if not path:
        return
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(
                {"text": text_n, "llm_note": llm_note, "llm_violations": llm_violations},
                fh,
            )
    except OSError:
        pass


def _prune_receipts(now):
    """Drop receipt files older than RECEIPT_TTL so the content-keyed set can't
    grow unbounded. Best-effort; a re-gated draft just refreshes its own file's
    mtime, so live drafts survive."""
    try:
        for name in os.listdir(RECEIPTS_DIR):
            path = os.path.join(RECEIPTS_DIR, name)
            try:
                if now - os.path.getmtime(path) > RECEIPT_TTL:
                    os.remove(path)
            except OSError:
                pass
    except OSError:
        pass


def _write_receipt(text, failed, judge_skipped=False):
    """Record a content-keyed PASS receipt so the Stop-hook gate and the outbound
    guard can confirm this exact text passed the full gate (judge included)
    without re-running the nondeterministic judge.

    Receipts are a SET, not a single file: one file per passing body, named by
    its normalized sha256, under RECEIPTS_DIR. That makes concurrent voice
    drafts safe - two sessions each drop their own receipt instead of clobbering
    one shared file, so one agent's PASS (or FAIL) can never invalidate
    another's gated draft. On FAIL we write nothing and delete nothing: a
    receipt for OTHER (already-passed) text is not ours to remove, and the
    failing text simply has no receipt of its own. When the judge did not run
    (--no-llm / ANTI_AI_NO_LLM) leave the set untouched, so the gate's own
    --no-llm diagnostic run cannot forge a receipt. Best-effort: never raises."""
    if judge_skipped or failed:
        return
    try:
        os.makedirs(RECEIPTS_DIR, exist_ok=True)
        digest = hashlib.sha256(_norm(text).encode("utf-8")).hexdigest()
        with open(os.path.join(RECEIPTS_DIR, digest), "w", encoding="utf-8") as fh:
            fh.write(str(int(time.time())))
        _prune_receipts(time.time())
    except OSError:
        pass


def main():
    text = sys.stdin.read()
    allowlist = load_allowlist()
    static = find_static_violations(text, allowlist)
    ctx = load_voice_context()

    # Convergence: within one session, an identical draft reuses the llm
    # verdict, and an edited draft is judged on its changed lines only.
    text_n = _norm(text)
    state = load_lint_state()
    changed_lines = None
    cached = None
    if state:
        if state.get("text") == text_n:
            cached = state
        else:
            prev_lines = {
                line for line in state.get("text", "").splitlines() if line.strip()
            }
            changed_lines = [
                line
                for line in text_n.splitlines()
                if line.strip() and line not in prev_lines
            ]

    llm_violations = []
    dropped_notes = []
    llm_note = None
    judge_skipped = False
    if cached is not None:
        llm_violations = list(cached.get("llm_violations", []))
        llm_note = (cached.get("llm_note") or "llm judge") + " [cached, draft unchanged]"
    else:
        judge = llm_judge(text, allowlist, ctx=ctx, changed_lines=changed_lines)
        if judge is None:
            judge_skipped = True
            llm_note = "llm judge: skipped"
        elif "error" in judge:
            # Fail CLOSED: a judge that could not run (all backends errored or
            # timed out) must never yield a PASS or a receipt.
            llm_note = f"llm judge: unavailable ({judge['error']})"
            llm_violations.append(
                f"llm judge did not run ({judge['error']}); failing closed "
                "(voice unverified, no PASS receipt written) - re-run the gate"
            )
        else:
            backend = judge.get("_backend", "?")
            verdict = str(judge.get("verdict", "")).upper()
            raw = judge.get("violations", []) if verdict == "FAIL" else []
            kept, dropped = (
                validate_llm_violations(raw, ctx) if ctx else (raw, [])
            )
            for v in dropped:
                dropped_notes.append(
                    "dropped (cites no rulebook rule): "
                    f"{(v.get('quote') or '')[:70]}  [{(v.get('rule') or '')[:70]}]"
                )
            for v in kept:
                quote = (v.get("quote") or "").strip()
                rule = (v.get("rule") or "").strip()
                fix = (v.get("fix") or "").strip()
                line = f"llm: {quote}".rstrip()
                if rule:
                    line += f"  [{rule}]"
                if fix:
                    line += f"  -> {fix}"
                llm_violations.append(line)
            if verdict == "FAIL" and not raw:
                llm_violations.append("llm: FAIL (no detail returned)")
            if llm_violations:
                llm_note = f"llm judge: FAIL (via {backend})"
            else:
                llm_note = f"llm judge: PASS (via {backend}"
                if dropped:
                    llm_note += f"; {len(dropped)} invented flag(s) dropped"
                llm_note += ")"
            save_lint_state(text_n, llm_note, llm_violations)

    failed = bool(static) or bool(llm_violations)
    _write_receipt(text, failed, judge_skipped)
    print("FAIL" if failed else "PASS")
    for v in static:
        print(f"- {v}")
    for v in llm_violations:
        print(f"- {v}")
    if llm_note:
        print(f"# {llm_note}")
    for note in dropped_notes:
        print(f"# {note}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

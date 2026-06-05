#!/usr/bin/env python3
"""Static-layer tests for check.py. Run: python3 test_check.py

No LLM, no network: these exercise find_static_violations directly. They lock in
the DOTALL fix (a cross-paragraph "from ... to ...," must not fire) and the
allowlist behavior.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check  # noqa: E402


def v(text, allowlist=None):
    return check.find_static_violations(text, allowlist or set())


def has(text, needle, allowlist=None):
    return any(needle in x for x in v(text, allowlist))


def main():
    # 1. DOTALL regression: "from" in one paragraph, "to" + "," in another.
    #    This used to fail the whole document. It must be clean now.
    doc = "We work backward from the goals we want.\n\nWe map that to business value, and measure it."
    assert not any("pattern" in x for x in v(doc)), v(doc)

    # 1b. Even on a single line, a plain range is not a tell.
    assert not any("pattern" in x for x in v("We grew from 10 to 40 facilities, adding three states.")), \
        v("We grew from 10 to 40 facilities, adding three states.")

    # 2. The actual false-range DOUBLING tell still fires.
    doc2 = "It spans from the big bang to dark matter, from soup to nuts."
    assert any("pattern" in x for x in v(doc2)), v(doc2)

    # 3. Dropped patterns no longer fire on plain prose.
    assert not has("we run more than 40 facilities, including aspen.", "pattern")
    assert not has("beyond the obvious wins, there is real risk here.", "pattern")

    # 4. Allowlist exempts a word and a phrase.
    assert has("a scalable system", "scalable")
    assert not has("a scalable system", "scalable", {"scalable"})
    assert has("In summary, we ship.", "in summary")
    assert not has("In summary, we ship.", "in summary", {"in summary"})

    # 5. Genuine tells still fail.
    assert has("let me delve into this", "delve")
    assert has("Furthermore, we win.", "furthermore")
    assert has("a dash — here", "—")

    # 6. A within-paragraph formula is still caught (per-line, not weakened).
    assert any("pattern" in x for x in v("This isn't just a tool, it's a platform.")), \
        v("This isn't just a tool, it's a platform.")

    print("all tests passed")


if __name__ == "__main__":
    main()

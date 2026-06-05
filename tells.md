# AI tells (strip every one)

The AI fingerprint: moves that carry no work and mark text as machine-written. None are needed for good writing. `check.py` holds the enforced enumeration (exact characters, words, phrases, regex). This file is the concept behind it. Avoid the whole family, not just the listed words, in every kind of writing.

## Punctuation
- No em dash or en dash. Use a comma, period, colon, or parentheses. This is the single most reliable AI tell.
- No semicolons unless the user asks for formal prose.
- No mechanical boldface scattered mid-sentence to fake emphasis.
- No decorative emoji in headings or bullets.
- Headings in sentence case, not Title Case.
- Straight quotes, not curly, when you control the output.

## Validation and sycophancy
Affirming the reader or their feelings carries no work. Cut the whole family, including paraphrases.
- "That's real" / "your concern is valid" / "you're not wrong" / "that makes sense"
- "I hear you" / "I completely understand" / "I appreciate you sharing"
- "Great question" / "You're absolutely right" / "I hope this helps"
Replace with the actual answer.

## Prefaces and signposting
Announcing what you are about to do instead of doing it.
- "Let me..." / "Here's..." / "Happy to help" / "Sure" / "Of course"
- "Let's dive in" / "Let's break it down" / "Here's what you need to know" / "Without further ado"
Delete and start with the content.

## Transition filler
Connectives with no content. Start the next sentence with its actual claim.
- Furthermore, Moreover, Additionally, Importantly, Notably, Consequently, Ultimately, Overall, In conclusion, In summary
- "It is worth noting" / "It is important to note" / "Keep in mind" / "As previously mentioned"

## Inflated vocabulary
Each stands in for a concrete thing. Replace it with the thing it hides.
- delve, robust, seamless, leverage, utilize, streamline, optimize, comprehensive, holistic, strategic, actionable, impactful, vibrant, tapestry, landscape, ecosystem, journey, unlock, empower, elevate, foster, navigate, cultivate, harness, spearhead, interplay
- "utilize" to "use"; "leverage" to the actual action; "robust" to the specific capability; "seamless" to the actual behavior; "streamline" to the removed step; "comprehensive" to the scope.

## Copula avoidance
Elaborate verbs standing in for is / are / has.
- "serves as", "stands as", "marks", "represents a", "boasts", "features", "offers"
- "The gallery serves as the exhibition space and boasts 3,000 sq ft" to "The gallery is the exhibition space and has 3,000 sq ft."

## Significance and legacy inflation
Turning an ordinary detail into a Broader Trend.
- "stands as a testament to", "marks a pivotal moment", "underscores its importance", "reflects a broader shift", "leaving an indelible mark"
- "marking a pivotal moment in the evolution of regional statistics" to "was created to publish statistics independently."

## Superficial -ing tails
A present-participle clause bolted on to fake depth.
- "..., highlighting the community's deep connection" / "..., underscoring its significance" / "..., reflecting a commitment to quality"
- Cut the tail, or replace it with the actual fact.

## Weasel attributions
An opinion pinned on a vague authority.
- "Experts argue", "Observers note", "Industry reports suggest", "Critics say", "It is widely believed", "Studies show" (with nothing cited)
- Name the source or drop the claim: "Experts believe it is crucial" to "a 2019 survey by [X] found..."

## Persuasive-authority tropes
Phrases that pretend to cut to a deeper truth and just restate the point with ceremony.
- "the real question is", "at its core", "what really matters", "fundamentally", "the heart of the matter", "make no mistake", "the truth is", "the reality is"
- Say the point plainly instead.

## Speculative gap-filling
Dressing a guess as fact when the real thing is not known. This also violates verify-don't-assume: do not invent plausible filler.
- "likely grew up", "maintains a low profile", "presumably", "as of my last update", "while details are scarce, it appears"
- State what is not known, or cut the section.

## Formula patterns
Rhetorical templates. Avoid the structure even when the words change.
- "This is not X. This is Y." / "Not X, but Y" / "It's not just X, it's Y"
- "Less X, more Y" / "Forget X. Focus on Y." / "X is dead. Y is the future."
- False ranges: "from the Big Bang to dark matter, from X to Y" where X and Y are not a real scale.
- Taglines: "X reimagined", "X made simple", "X done right", "X, without the Y", "X at scale".

## List reflexes
- Don't default to three bullets or three adjectives. Use the number the content needs.
- No paired adjective sets: "fast, simple, and secure", "scalable, reliable, and secure".
- No inline-header lists that restate the header: "**Performance:** Performance is improved." Write it as prose.
- No fragmented header: a heading followed by a one-line paragraph that just repeats it.

## Hedging and filler
- "in order to" to "to"; "due to the fact that" to "because"; "at this point in time" to "now"; "has the ability to" to "can".
- Kill stacked hedges: "could potentially possibly" to one word or none.

## Self-description and meta
- Don't say the writing is concise, direct, human, polished, or authentic.
- Don't narrate a change in docs that are not changelogs ("this was added to replace..."). Describe what is, not what changed.
- Don't explain these rules to the user unless asked.

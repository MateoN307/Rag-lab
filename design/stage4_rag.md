# Stage 4 — `rag.py`

## What this stage is, as a black box

```
INPUT:  a question string from the user
OUTPUT: a grounded answer (string) — plus, visibly, the context that
        grounded it
```

This is where every previous stage's output becomes someone's *experience*
of using a RAG system: ask a question about your own notes, watch it find
relevant context, watch an LLM reason over that context instead of just
hallucinating from its training data.

## Required contract

### Required entry point
```python
def answer(question: str, k: int = 5) -> ...:
    """
    Retrieve the top-k relevant chunks for `question` (via Stage 3),
    build a grounded prompt around them, send it to the local LLM,
    and return both the final answer AND the retrieved context that
    produced it — the user needs to be able to see *why* the model
    said what it said.
    """
```
The exact return shape (string vs. dict vs. dataclass with `.answer` and
`.sources`) is yours — but it must expose **both** the answer and the
retrieved chunks, not just the answer alone. Hiding the retrieval step
defeats the purpose of building this yourself.

### Non-negotiable behaviors
- Generation must hit your **local** Ollama instance (`llama3.2`) — no
  external API
- The prompt must clearly separate "context retrieved from the vault" from
  "the user's question," and must instruct the model to ground its answer
  in that context (and to admit when the context doesn't contain an answer,
  rather than confidently making one up)
- When run directly, the retrieved chunks (with sources + scores) and the
  final answer must both be visible — side by side, not just the answer

## Open — these are genuinely yours to decide
- How you take input (CLI arg, `input()`, a small loop for multiple
  questions — your call)
- The exact prompt template/wording — this is actually one of the more
  interesting design surfaces in the whole project; experiment with it
- What `k` should default to, and whether you let the user change it
- Whether you stream the model's response or wait for the full output

## "Play" experiments worth running once it works end-to-end
These are the actual payoff of building this yourself — go poke at it:
- Ask something your vault definitely **doesn't** contain. Does it say "I
  don't know," or does it confidently make something up anyway? What does
  that tell you about how much the prompt wording matters?
- Ask something whose answer is **split across two notes** — does the model
  successfully stitch the pieces together, or does it only use one?
- Try changing `k` (3 vs 5 vs 10) — does answer quality change? Does
  irrelevant context ever *hurt* the answer rather than help it?
- (Stretch) Try re-ranking: retrieve more candidates than you need, reorder
  them by some heuristic, and only inject the best few — does it help?

## Design decisions (November 2026)
**Contract.** `answer(question, k=5, db_dir, prompt_version, model)` returns
`Answer(text, sources, truncated)`: the model's text, the chunks it was given,
and whether the prompt had to be cut.

**Prompt.** A system message holds the rules: answer only from the excerpts;
judge whether each one states the answer directly, implies it, or is
unrelated; sound confident only for direct, high-match evidence; admit when
the notes don't answer; reply in the question's language; end with a Sources
section. The user message holds the numbered excerpts (match level, note
path, text), then the question. *Considered and rejected:* giving the model
raw scores, which a small model can't interpret, so code turns them into
high, medium or low; and having the model write note paths, which small
models garble, so it cites excerpt numbers and the app prints the real paths.

**Match labels are hints, not a threshold.** High ≥ 0.55, medium ≥ 0.50,
otherwise low, provisional. The evaluation showed why no score cutoff can
decide relevance on its own: unanswerable questions reached 0.630 while the
median answerable question's top score was 0.630, mostly because a Spanish
question scores high against any Spanish note.

**Model, prompt and k were chosen by measurement** (see the Stage 5
results): `llama3.1:8b` over `llama3.2` (3B); prompt v2 as the default,
trading about 7 points of key facts for perfect Sources formatting and twice
as many honest "Sources: none"; and k = 5 over 3 and 10.

**Context window 16,384 tokens.** Ollama's default of 4,096 silently cut the
longest prompts, starting from the beginning, which is where the rules are.
The window is now set explicitly, and any prompt that still fills it is
reported as truncated. Temperature is 0, so the same question gets the same
answer and prompt versions can be compared fairly.

**Future work.** Optionally adding the model's general knowledge in a
separate, clearly labelled section, and an automatic judge to replace phrase
matching in the evaluation.

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

# Stage 2 — `embedder.py`

## What this stage is, as a black box

```
INPUT:  a string of text  (and, separately: pairs of vectors to compare)
OUTPUT: a vector (list of floats)   |   a similarity score (float)
```

Stage 3 needs a way to turn arbitrary text — chunk text *and* user queries —
into vectors it can store/compare. This stage is where that capability lives,
and where you build the comparison primitive (cosine similarity) by hand so
you actually understand what the vector DB is doing for you later.

## Required contract

### Required entry points
```python
def embed_text(text: str) -> list[float]:
    """
    Return the embedding vector for `text`, using Ollama's
    `nomic-embed-text` model (768-dim, mean-pooled).
    """

def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Return the cosine similarity between two equal-length vectors:
        (A · B) / (||A|| * ||B||)
    Implemented by hand — dot product, magnitudes, division — no
    numpy/scipy shortcuts for the formula itself.
    """
```
These two names/signatures matter: Stage 3 (and your own sanity checks) will
call `embed_text` on both chunks and queries, and may reuse `cosine_similarity`
when comparing vectors directly (independent of whatever Chroma does
internally).

### Non-negotiable behaviors
- `embed_text` must hit your **local** Ollama instance — no external API
  calls, no API keys, the whole point is a self-hosted pipeline
- `cosine_similarity` must be a from-scratch implementation (loops/
  comprehensions over the float lists are fine — that's the point)

## Open — these are genuinely yours to decide
- How you sanity-check the embedder when run directly (which test phrases,
  how many, how you present the similarity matrix)
- Whether you batch embedding calls or do them one at a time
- Any helper functions you want around vector math (magnitude, dot product
  as their own named functions, etc.) — break it down however makes the
  logic clearest to you
- Error handling if Ollama isn't running / the model isn't pulled — up to
  you whether that's worth handling now or later

## A thing you may run into
Some chunks may behave oddly when you try to embed them — either erroring,
getting truncated, or producing suspicious vectors. If you hit that: look
closely at *what kind of content* is in the chunk that's misbehaving versus
ones that aren't. There's a real, explainable reason — bring back what you
notice and we'll dig into the "why" together rather than me spoiling it now.

## Reference data point (for your own sanity-checking)
A previous run produced: cat/mat vs feline/rug ≈ 0.72, vs stock market ≈ 0.39
— related concepts scoring meaningfully higher than unrelated ones is the
signal you're looking for, not these exact numbers.

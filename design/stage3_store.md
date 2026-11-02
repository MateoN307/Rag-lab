# Stage 3 — `store.py`

## What this stage is, as a black box

```
INPUT (build):    the vault (via Stage 1 + Stage 2)
INPUT (query):    a question string
OUTPUT (query):   the top-K most similar chunks, with enough info to
                  trace each one back to its source and judge its relevance
```

This is the layer where the HNSW concepts from the lecture stop being theory
and start being something you can actually observe — Chroma is doing
approximate nearest-neighbor search under the hood instead of comparing your
query against every stored vector by brute force.

## Required contract

### Required entry points
```python
def build_index() -> None:
    """
    Ensure the persistent vector index exists and is populated:
    chunk the vault, embed each chunk, and store it with enough
    metadata to identify it later. Should be safe to call repeatedly
    without duplicating work (i.e. don't re-embed everything every run).
    """

def query_index(question: str, k: int = 5) -> list[...]:
    """
    Embed `question`, retrieve the top-k most similar stored chunks,
    and return them — each result needs to carry at least: the chunk
    text, its source/position metadata, and a similarity score.
    """
```
Stage 4 will call `query_index` directly — its name, and the fact that each
returned result exposes text + source + score, are the parts that need to
stay stable.

### Non-negotiable behaviors
- The index must **persist to disk** between runs (a fresh Python process
  should be able to query without rebuilding from scratch)
- Each stored entry must retain a path back to its original chunk's
  `source` and `index` (from Stage 1) — retrieval is useless if you can't
  tell the user *where* an answer came from
- `query_index` must return results **ranked by similarity**, with the
  score visible/accessible — not just a bag of texts

## Open — these are genuinely yours to decide
- Whether you call `embed_text` from Stage 2 yourself, or wire Chroma up to
  embed via its own embedding-function interface (both are legitimate —
  worth understanding the tradeoff: who controls the embedding model, and
  where does the "768-dim mean-pooled vector" guarantee actually come from?)
- Where on disk the index lives, how you check "is it already built," what
  you do if the vault has changed since the last build (rebuild everything?
  diff and update? — totally fine to punt on this for now and just note it)
- What exactly a "result" looks like as a Python object (dict, dataclass,
  Chroma's native return type passed through, etc.)
- What you print when run directly to convince yourself retrieval works

## Things worth noticing once it's running (bring back what you find)
- Try a query on something you know is in your vault — does the top result
  make sense? Does the similarity score match your gut feeling?
- Try a query on something your vault almost certainly *doesn't* contain —
  what comes back, and what does the score look like compared to a real hit?
- Try a query where the answer might be split across two notes/chunks —
  do both surface in your top-K?

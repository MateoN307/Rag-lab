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

## Design decisions (November 2026)
**Storage.** A persistent Chroma database in `db_dir` (default `app/db/`),
collection `vault_chunks`, comparing vectors by **cosine** distance, so
similarity = 1 − distance. A helper opens it when needed, never at import time
(importing the store must not create a database). Each chunk is stored as id
`"source#index"`, its vector from `embed_text` (not Chroma's built-in
embedding model, so one place decides how text becomes a vector), its text,
and metadata `{source, index, hash}`.

**Not redoing work.** Every note gets a fingerprint: the sha256 of its raw
bytes, stored in each of its chunks' metadata. Each run compares `on_disk`
(`{source: hash}` for the notes from `find_md_files`, the shared note list
from the Stage 1 redesign) with `in_store` (`{source: hash}` read from the
stored metadata) and sorts each note into **unchanged** (skip), **edited**
(delete its chunks, then add), **new** (add) or **deleted** (delete).
- *Per note, not per chunk:* one edited word shifts every later chunk
  boundary, so per-chunk comparison would flag almost everything anyway.
- *Raw bytes, not cleaned text:* simpler, and the store doesn't depend on the
  chunker's internals. The cost is that a frontmatter-only edit re-embeds that
  note, and changes to the cleaning rules, chunk settings or embedding model
  aren't detected. Those cases will be covered by a planned "rebuild
  everything" option.
- Renaming or moving a note shows up as one deleted plus one new note.

**The comparison loop.** One loop over the union of both dicts' paths, looking
each one up in both dicts. *Considered and rejected:* looping over `on_disk`
while removing each path from `in_store`, then deleting whatever was left.
It's correct, but it empties `in_store` as it goes and splits the rules across
two places. Also rejected: a sorted merge walk over both lists, which needs
sorting first, whereas dicts already give constant-time lookups.

**Edited notes are deleted before being re-added**, because Chroma's `add()`
silently ignores ids that already exist: without the delete, the old chunks
would stay.

**One `add` per note.** All of a note's chunks are embedded first, then stored
in a single call. If anything fails mid-note, nothing of that note is stored,
so the next run sees it as new and redoes it cleanly. This happened in
practice: the first build crashed and left 90 notes stored, each one
complete.

**Oversized chunks.** When the model rejects a chunk as too long, the store
re-chunks the *whole* note with `chunk_words × 0.75` and tries again
(450 → 338 → 254 → …), down to a floor of 20 words. Only that specific error
triggers a retry; any other error (for example, Ollama not running) stops the
build as before. Different notes ending up with different chunk lengths is
safe: fingerprints are per note, deletion is by source, ids are
`source#index`, and cosine similarity doesn't depend on chunk length.
*Considered and rejected:* a token-aware chunker (see Stage 1); lowering the
chunk length for every note (changes all of them to fix two chunks); and
embedding only the first part of an oversized chunk (the end of that chunk
would never be found by search).

**Inputs and summary.** `build_index(vault_path=VAULT_PATH, db_dir=DB_DIR)`:
the defaults keep the original `build_index()` call working, and the
parameters let tests use a temporary vault and database. A missing
`VAULT_PATH` raises a clear error. It returns a summary: counts of `new`,
`edited`, `deleted` and `unchanged` notes, plus `empty` (notes that produce no
chunks), `shrunk` (`{path: chunk_words}` for notes that needed smaller chunks)
and `too_dense` (notes that couldn't fit even at 20 words). Notes with no
chunks count only as `empty`, so a run where nothing changed reports zero new,
edited and deleted.

**Planned after the MVP.** Separate knowledge sets: the parameters already
allow one database per vault, and the rule to document is *one vault per
database*, because pointing a second vault at the same database would delete
the first vault's notes as "missing". Also the "rebuild everything" option.

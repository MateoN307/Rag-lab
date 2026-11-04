# Stage 1 — `chunker.py`

## What this stage is, as a black box

```
INPUT:  a directory of markdown files (the vault)
OUTPUT: a flat list of chunk records ready to be embedded in Stage 2
```

Stage 2 (`embedder.py`) needs to take whatever this stage produces and embed
each piece of text individually. Stage 3 (`store.py`) needs to store each
embedded piece alongside enough metadata to trace it back to its source file
and position. So the **shape of the output is the contract** — everything
about *how* you get there is yours to decide.

## Required contract

### Output shape (non-negotiable — Stage 2/3 depend on this)
A flat list of records, where each record carries at minimum:
- the chunk's **text** (a string)
- the **source** it came from, in a form that lets a human find the
  original note again (relative path is the obvious choice, but the exact
  representation is up to you)
- the chunk's **position** within its source (so multiple chunks from the
  same file stay ordered and distinguishable)

You can use dicts, dataclasses, namedtuples, whatever — just be consistent,
and document the shape at the top of the file so Stage 2 knows what to expect.

**Decision: `Chunk` dataclass, no default field values.**
```python
@dataclass
class Chunk:
    text: str
    source: str
    index: int
```
No defaults are given for any field, which means `Chunk()` alone is invalid —
Python requires `text`, `source`, and `index` all be supplied at construction
time (`Chunk(text=..., source=..., index=...)`). This is intentional: it
guarantees that every `Chunk` that exists is fully formed the moment it's
created — there's no "empty chunk" state floating around that downstream code
would need to special-case or guard against. Chunks get assembled by gathering
all three values first, then constructing in one shot — not built blank and
filled in field-by-field.

### Required entry point
```python
def chunk_dir(dir_path: str) -> list[Chunk]:
    """
    Walk `dir_path`, process every .md file, and return the flat list
    of Chunk records described above.
    """
```
Named `chunk_dir` (not `chunk_vault`) because the walking/cleaning/splitting
logic is generic to any directory of markdown files — it isn't inherently tied
to Mateo's Obsidian vault, and may get reused outside this project later. This
is the function Stage 3 will eventually call to (re)build the index — its name
and signature need to stay stable so the pipeline connects.

### Non-negotiable behaviors
- **No chunking library.** The word-split + overlap logic must be your own —
  this is the part of the lab that's actually about understanding how
  chunking works, not about calling `langchain.text_splitter`.
- **Word-accurate splitting**, not character-based. Cosine similarity later
  cares about *semantic* chunks, and cutting mid-word produces garbage
  embeddings.
- **No data loss on edge cases.** A file shorter than one chunk still has to
  produce at least one chunk — never silently drop content.

## Open — these are genuinely yours to decide
- Exact chunk size and overlap (we discussed ~400 words / ~50-word overlap
  as a starting point last time, but you can pick your own and change it
  later — this is a tunable, not a law)
- How aggressively to clean the markdown (frontmatter, `[[wiki links]]`,
  `![[embeds]]` are the obvious noise — there may be more you discover by
  looking at real notes from the vault)
- Whether to expose helper functions (e.g. a standalone "clean this text" or
  "split this text into chunks" function) or keep everything internal to
  `chunk_vault` — your call, as long as the public contract above holds
- What you print/log when running the file directly, to sanity-check your
  own output before wiring it into Stage 2

## Fix: duplicate tail chunk (November 2026)
**Problem.** Each chunk is `words[start : start + 450]`, and the next one starts
400 words later. The loop kept going while the next chunk's *start* was still
inside the note, so a note ending 1 to 50 words past a multiple of 400 got an
extra last chunk made only of words it already had. A 420-word note gave words
1–420 and then 401–420 again. That chunk adds nothing, wastes an embedding
call, and at query time it can take a top-k slot from a genuinely different
chunk.

**Fix.** After saving a chunk, stop if it reached the end of the note
(`end >= total`). It's `>=` and not `==` because the slice silently clips when
`end` runs past the list. The `while start < total` condition stays, since it's
what makes an empty note produce zero chunks.

**Tests.** `overlap_420` and `exact_450` fail on the old code and pass now.
`one_over_451` and `over_461` are guards: a real second chunk must still be
made.

## Redesign: one shared list of notes (November 2026)
**Problem.** While designing Stage 3's `build_index`, the store needed the
same list of notes as `chunk_dir`, with paths spelled exactly like each
chunk's `source`. If they ever differ, every note looks both new and deleted
on each run, and the whole vault gets re-embedded. That logic lived inside
`chunk_dir`, so the store would have had to copy it, and two copies can drift
apart.

**Change.** The folder walk moved out of `chunk_dir` into a new public
function, `find_md_files(dir_path)`, which returns every `.md` path relative
to `dir_path`. Both `chunk_dir` and the store call it, so the set of notes and
the path strings are defined in one place. The one-folder helper was renamed
`_md_files_in_folder`, so the two names differ by more than an underscore. The
"not a directory" check moved into `find_md_files`, so every caller gets it.
The list of callers lives here rather than in the function's docstring, so
the code's comments can't go stale as new callers appear.

**Proof nothing changed.** It's a refactor: the existing `chunk_dir` tests
pass unchanged, and on a real vault the old and new `chunk_dir` produce
identical chunks. New tests cover what `find_md_files` adds: reaching every
depth, backtracking out of dead-end folders into siblings, keeping same-named
notes in different folders apart, and paths relative to the folder passed in.

## Vault location
Machine-specific, so it isn't in the repo: set `VAULT_PATH` in `.env` (see `.env.example`).

## A thing to keep an eye out for (you'll understand why once you hit Stage 2)
Not every chunk of text is created equal once it gets to the embedding
model — some content is structurally denser than plain prose. Keep your
chunker's output inspectable (e.g. easy to print/sample specific chunks),
because you may need to come back and look at *which* chunks are unusual
once you start embedding them.

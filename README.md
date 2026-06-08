# Rag Lab

A learning project where I'm building a Retrieval-Augmented Generation (RAG)
system from scratch, piece by piece, in order to actually understand how
memory retrieval for LLMs works under the hood — rather than just calling a
library that does it for me.

## What I'm building

The pipeline is split into stages, each one a self-contained piece of the
overall flow:

```
chunk -> embed -> store -> retrieve -> inject -> answer
```

1. **`chunker.py`** — walks a directory of markdown notes (my personal
   Obsidian vault), cleans each note up (strips frontmatter, resolves
   `[[wiki links]]`, removes `![[image embeds]]`), and splits the cleaned
   text into overlapping word-based chunks ready to be embedded.
2. **`embedder.py`** *(in progress)* — turns each chunk's text into a vector
   embedding using an embedding model.
3. **`store.py`** *(planned)* — stores the embedded chunks (plus their
   metadata) so they can be searched later.
4. **`rag.py`** *(planned)* — ties it all together: takes a question, finds
   the most relevant chunks, injects them into a prompt, and gets an answer
   from an LLM.

Specs for each stage live in [`specs/`](./specs).

## How I'm using AI for this

I'm writing this project to learn — both how RAG systems work conceptually,
and how to write Python (which I'm new to; my background is mostly C/C++).
So the role I've given the AI here is intentionally narrow:

- **I describe the logic in plain language**, and the AI translates that
  description into Python — it does not design the solution or add anything
  I haven't asked for.
- **The AI explains the Python syntax** as it writes it, since I'm learning
  the language by seeing it used in a real project.
- **When something is ambiguous, the AI asks rather than assumes**, so the
  design decisions stay mine.

The full set of ground rules for this collaboration is written out in
[`specs/collaboration_mode.md`](./specs/collaboration_mode.md).

## Project layout

```
app/        the actual pipeline code (chunker.py, etc.)
specs/      design specs for each stage, plus the AI collaboration rules
scripts/    small helper/dev tools (e.g. test-fixture generators)
tests/      fixtures and manual test data used by the app's _test_* functions
```

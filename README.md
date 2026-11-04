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
2. **`embedder.py`** *(done)* — turns each chunk's text into a vector
   embedding using an embedding model.
3. **`store.py`** *(in progress)* — stores the embedded chunks (plus their
   metadata) so they can be searched later.
4. **`rag.py`** *(planned)* — ties it all together: takes a question, finds
   the most relevant chunks, injects them into a prompt, and gets an answer
   from an LLM.

Specs for each stage live in [`design/`](./design).

## How I'm using AI for this

I'm writing this project to learn two things: how RAG systems work conceptually,
and how to design a project properly (planning each stage in a spec, building
it piece by piece, and testing it before moving on). So the role I've given the
AI here is intentionally narrow:

- **I describe the logic in plain language**, and the AI translates that
  description into Python — it does not design the solution or add anything
  I haven't asked for.
- **The AI explains the Python syntax** as it writes it, since I'm learning
  the language by seeing it used in a real project.
- **When something is ambiguous, the AI asks rather than assumes**, so the
  design decisions stay mine.

The full set of ground rules for this collaboration is written out in
[`design/collaboration_mode.md`](./design/collaboration_mode.md).

## Project layout

```
app/        the actual pipeline code (chunker.py, etc.)
design/     design specs for each stage, plus the AI collaboration rules
scripts/    small helper/dev tools (e.g. test-fixture generators)
tests/      pytest tests (run with uv run pytest) and the fixture files they read
```

## A note on personal paths

This repo intentionally avoids hardcoding any machine-specific absolute paths
(home directories, personal vault locations, etc.):
- Paths to things that live *inside* the repo (like the test fixtures) are
  computed relative to the source file itself.
- Anything genuinely personal (e.g. the location of my Obsidian vault) is
  read from a local `.env` file, which is gitignored. See `.env.example` for
  the expected format — copy it to `.env` and fill in your own values.

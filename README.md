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

1. **`chunker.py`** *(done)* — walks a directory of markdown notes (my
   personal Obsidian vault), cleans each note up (strips frontmatter, resolves
   `[[wiki links]]`, removes `![[image embeds]]` and table separator rows), and
   splits the cleaned text into overlapping word-based chunks ready to be
   embedded.
2. **`embedder.py`** *(done)* — turns each chunk's text into a vector
   embedding using a local embedding model (`nomic-embed-text` via Ollama).
3. **`store.py`** *(done)* — keeps a persistent vector index (Chroma) in sync
   with the vault, re-embedding only the notes that changed, and finds the
   chunks most similar to a question.
4. **`rag.py`** *(done)* — takes a question, retrieves the most relevant
   chunks, and asks a local LLM (`llama3.1:8b` via Ollama) to answer from
   them, showing which notes it used and how much it trusts each one.
5. **`scripts/evaluate.py`** *(done)* — scores the whole pipeline against a
   fixed set of questions, so every change is measured instead of judged by
   eye.

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

## Running it

Everything runs locally: no API keys, and nothing leaves the machine.

1. Install [uv](https://docs.astral.sh/uv/) and [Ollama](https://ollama.com),
   then pull the two models:
   ```
   ollama pull nomic-embed-text
   ollama pull llama3.1:8b
   ```
2. Install the dependencies, and point the project at your notes by copying
   `.env.example` to `.env` and setting `VAULT_PATH`:
   ```
   uv sync
   ```
3. Ask questions (the first run indexes the vault; later runs only re-index
   notes that changed):
   ```
   uv run python app/rag.py
   ```
4. Run the tests, or score the pipeline against your own evaluation set (see
   `design/stage5_evaluation.md`):
   ```
   uv run pytest
   uv run python scripts/evaluate.py --name my-run --answers
   ```

## Results

Measured on 32 questions about my notes (24 answerable, 8 not):

| What | Result |
|---|---|
| Search finds a right note in the top 5 | 83% of answerable questions |
| Key facts in the answer, when search found the note | 94% (`llama3.1:8b`, prompt v1) |
| Answers ending in a correct Sources section | 94% (prompt v3, the default; 100% with v2) |
| Questions the notes can't answer, admitted as such | 100% |

What measuring taught me:
- **A bigger model followed the rules a smaller one couldn't.** Extra prompt
  rules made the 3B model worse at everything; the 8B model used them to
  reach 100% correctly formatted sources.
- **More context isn't better.** Five excerpts beat three (missing facts) and
  ten (the model lost focus).
- **The model's capacity is now the ceiling.** Every prompt or context change
  traded one score for another; none improved them all at once. The next
  gains need a larger model or better search.
- **Silent failures hide in the plumbing.** Ollama's default context window
  was quietly cutting the longest prompts, instructions included. Fixing it,
  and flagging truncation, raised the format score from 94% to 100%.

## Try it with the demo vault

`demo/vault/` holds 30 invented notes (a fictional engineering student's
courses, plans, recipes and guides, a few in Spanish) and
`demo/questions.json` holds 32 evaluation questions about them, so anyone can
reproduce the results. The demo gets its own database folder; never point two
vaults at the same one, or the second build deletes the first vault's notes.

```
VAULT_PATH=demo/vault DB_DIR=demo/db SKIP_FOLDERS=Templates uv run python app/rag.py
```

Run that once to build the demo index (and ask it questions), then score it:

```
VAULT_PATH=demo/vault DB_DIR=demo/db SKIP_FOLDERS=Templates EVAL_PATH=demo/questions.json uv run python scripts/evaluate.py --name demo --answers
```

| | Demo vault | My real vault |
|---|---|---|
| Right note in the top 5 | 96% | 83% |
| MRR | 0.844 | 0.605 |
| Key facts in the answer | 81% | 77% |
| Correct Sources section | 94% | 94% |
| Unanswerable questions admitted | 100% | 100% |

Search does much better on the demo because invented notes are tidy and
on-topic, while real notes mix languages, tables, HTML and half-finished
drafts. That gap is why thresholds and tuning should be measured on real
notes. Key facts are matched word for word, so the 81% undercounts: three
more answers were correct but phrased differently (for example "July 1,
2027" for 2027-07-01).

## Project layout

```
app/        the actual pipeline code (chunker.py, etc.)
design/     design specs for each stage, plus the AI collaboration rules
scripts/    small helper/dev tools (test-fixture generator, evaluation script)
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

## License

MIT, see [`LICENSE`](./LICENSE).

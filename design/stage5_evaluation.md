# Stage 5 — Evaluation and polish

## What this stage is, as a black box

```
INPUT:  a private evaluation set (questions about the vault, each with the
        notes and key facts that answer it, plus questions it can't answer)
        + one named configuration (prompt version, model, retrieval options, k)
OUTPUT: a scorecard of numbers that can be compared across configurations,
        and a polished tool that's ready to share
```

## Why this stage exists
The first end-to-end experiments showed two things. First, judging by eye
doesn't work: a prompt change fixed some answers and broke others, and with
four questions there was no way to tell a real improvement from luck. Second,
a bad answer has two possible causes. **Retrieval** can fail (the right note
isn't among the chunks), or **answering** can fail (the note is there but the
model mishandles it). Fixing the wrong one wastes time, so the two are
measured separately.

## The evaluation set
- **Private, never committed:** it's made of questions about personal notes.
  Its location is read from `.env` (`EVAL_PATH`), like `VAULT_PATH`.
- **About 20 answerable questions**, spread across the kinds of notes in the
  vault: course summaries, personal notes, tables, LaTeX, Spanish, and answers
  spread across several notes. Each one lists the note(s) that answer it, and
  1–3 **key facts** the answer must contain.
- **About 8 unanswerable questions:** general knowledge the model might know
  from its training, plus personal-sounding questions the vault doesn't cover.
- Claude drafts candidate questions from the vault and gives each one's note
  path; Mateo checks every one against the actual note before it's accepted.

**Format:** a JSON file (read with Python's built-in `json` module, so no new
dependency) holding a list of questions, each like:

```json
{"id": "trip-booking", "question": "what do I need to book for the trip?",
 "kind": "answerable", "sources": ["Personal/Trip.md"],
 "key_facts": ["ferry"], "tests": "personal to-do list"}
```

`kind` is `"answerable"` or `"unanswerable"`; `sources` are note paths
relative to the vault (empty for unanswerable questions); `key_facts` are
checked case-insensitively; `tests` records why the question is in the set.

## What gets measured

| Layer | Measure | Meaning |
|---|---|---|
| Retrieval | **hit@5, hit@10** | share of answerable questions with a right note in the top 5 / 10 |
| Retrieval | **MRR** | mean of 1/rank of the first right note (1st → 1, 2nd → 0.5, …): rewards ranking it high |
| Retrieval | **top score, answerable vs unanswerable** | where the high/medium/low bands should sit |
| Answers | **key-fact recall** | share of key facts present in the answer |
| Answers | **sources format** | the answer ends with a correctly formatted Sources section |
| Answers | **unanswerable handled** | says it couldn't find it, and writes "Sources: none" |
| Answers | **invented facts** | reviewed by hand, for answers flagged by the checks above |

Retrieval measures need no language model and take seconds; answer measures
run the model on every question and take a few minutes. Key facts are checked
as text matches, which is crude: a correct answer phrased differently, or in
another language, can be missed. That's why the flagged answers get reviewed
by hand.

## Rules for experiments
1. Measure a **baseline** first.
2. Change **one thing at a time**, at temperature 0, against the same
   evaluation set.
3. Every configuration has a **name** (for example: prompt v2, llama3.2,
   k=5), and its full results are saved privately with the date. The summary
   table of results goes in this document.
4. Retrieval variants that change what gets embedded are built into their
   **own database folder**, so the real index is never disturbed (the `db_dir`
   parameter from Stage 3).
5. A change is kept only if it improves what it targets without clearly
   hurting another measure. Borderline cases get decided explicitly and
   written down.

## Planned experiments, in order
1. **Baseline:** prompt v1 and v2, `llama3.2`, k = 5.
2. **Retrieval:** stripping HTML tags, starting each chunk with its note's
   title, the model's task prefixes, k = 5 vs 10. Then the high/medium/low
   bands get set from the measured score separation.
3. **Answers:** prompt iterations, then model size: `llama3.2` (3B) vs
   `llama3.1` (8B).

## Polish before calling the project done
- Ctrl+C and Ctrl+D exit cleanly instead of showing a traceback.
- A setting listing folders to leave out of the index (default: the templates
  folder), applied in `find_md_files` so the chunker and the store both respect
  it. Measured: leaving the templates out didn't change hit@5, hit@10 or MRR,
  but removed 6 template chunks from the top-5 context, mostly for questions
  the vault can't answer.
- README: how to set it up and run it, the status of each stage, and a
  summary of the results.
- A design-decisions section for Stage 4.
- A **demo vault** of invented notes with its own public evaluation set, so
  anyone can clone the project and reproduce the results.
- A license when the repository goes public.

## Results (November 2026)
Retrieval (32 questions): hit@5 83%, hit@10 88%, MRR 0.605. Leaving out the
templates didn't change these, but removed 6 template chunks from the top-5
context.

| Model | Prompt | k | Window | Key facts | Sources format | Admitted | "Sources: none" |
|---|---|---|---|---|---|---|---|
| llama3.2 (3B) | v1 | 5 | 4,096 | 72% | 66% | 100% | 0% |
| llama3.2 (3B) | v2 | 5 | 4,096 | 64% | 59% | 100% | 0% |
| llama3.1 (8B) | v1 | 5 | 16,384 | 79% | 84% | 100% | 25% |
| llama3.1 (8B) | v2 | 5 | 16,384 | 72% | **100%** | 100% | 50% |
| llama3.1 (8B) | v2 | 3 | 16,384 | 62% | 100% | 100% | 50% |
| llama3.1 (8B) | v2 | 10 | 16,384 | 59% | 94% | 100% | 12% |
| llama3.1 (8B) | **v3** (default) | **5** | 16,384 | 77% | 94% | 100% | **62%** |

When search put the right note in the top 5 (20 of 24 answerable questions),
the 8B model with v1 found 94% of the key facts. When it didn't, every
configuration got about 14%. Search, not the model, is now the main limit.
The answer checks match phrases, which missed correct admissions three times
(fixed by hand each time); an automatic judge is the planned replacement.

**Conclusion: the model's capacity is now the limit on the answer side.**
Every attempt to get more out of `llama3.1:8b` traded one measure for
another. More rules (v2) bought format and honesty but cost content. More
context (k = 10) lost focus, and less (k = 3) lost facts. v3 recovered most of
v1's content and gave the most honest "Sources: none" (62%), but dropped two
Sources sections. No prompt or k reached the best of every column at once.
Further gains need a larger model, or better retrieval: the questions search
misses are out of reach for any prompt.

## Decided
- **Evaluation-set format:** JSON, as above.
- **Where the evaluation script lives:** `scripts/evaluate.py`. It measures
  the pipeline rather than being part of it, so it sits with the other
  development tools, not in `app/`.

## Open — to decide while building
- Whether to add an automatic judge (a second model grading answers) once the
  manual reviews show what goes wrong.

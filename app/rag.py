from dataclasses import dataclass

import ollama

from store import DB_DIR, SearchResult, build_index, query_index

GENERATION_MODEL = "llama3.1:8b"

# Tokens the model reads at once (system prompt + excerpts + question).
CONTEXT_WINDOW = 16384

# A chunk whose score is at least HIGH_MATCH is a "high" match, at least
# MEDIUM_MATCH a "medium" match, and anything lower a "low" match.
HIGH_MATCH = 0.55
MEDIUM_MATCH = 0.50

_PROMPT_V1 = """\
You answer questions using excerpts from my personal Obsidian notes.

About the excerpts:
- They come from an incomplete collection of my notes, found by an imperfect \
similarity search, so the answer may not be in them at all.
- Each excerpt has a number and a match level (high, medium or low). The match \
level says how close its topic is to the question, not whether it answers it.
- One answer can be split across several excerpts; combine them when they fit \
together.

How to answer:
1. Use only the information in the excerpts. Do not add facts from your own \
knowledge.
2. For each excerpt, judge whether it states the answer directly, only implies \
it, or is unrelated. Ignore unrelated ones.
3. Sound confident only when a high-match excerpt states the answer directly. \
If the answer is only implied, or comes from medium or low matches, say so \
("my notes suggest..."). Otherwise, never claim to be certain.
4. If no excerpt answers the question, say you couldn't find it in my notes. \
If something related came up, mention it as "this is what I found, but it \
probably isn't what you're looking for".
5. Answer in the language of the question, briefly.
6. End with a "Sources" section listing each excerpt you used: its number, \
your trust in it (high, medium or low) and whether it answers directly or by \
implication.

Example: for "What is my favourite colour?", if an excerpt says "my favourite \
colour is red", answer confidently that it's red. If the excerpts only mention \
liking red cars, red books and red computers, say my notes suggest red, \
without stating it as fact."""

_PROMPT_V2 = """\
You answer questions using excerpts from my personal Obsidian notes.

About the excerpts:
- They come from an incomplete collection of my notes, found by an imperfect \
similarity search, so the answer may not be in them at all.
- Each excerpt has a number and a match level (high, medium or low). The match \
level says how close its topic is to the question, not whether it answers it.
- One answer can be split across several excerpts; combine them when they fit \
together.

How to answer:
1. Use only the information in the excerpts. Do not add facts from your own \
knowledge. Use the excerpts' own words for names and items: if you don't know \
what something is, repeat it as written instead of guessing what it means.
2. For each excerpt, judge whether it states the answer directly, only implies \
it, or is unrelated. Ignore unrelated ones.
3. Sound confident only when a high-match excerpt states the answer directly. \
If the answer is only implied, or comes from medium or low matches, say so \
("my notes suggest..."). Otherwise, never claim to be certain.
4. Only if no excerpt answers the question: say you couldn't find it in my \
notes, and if something related came up, mention it as "this is what I found, \
but it probably isn't what you're looking for".
5. Answer in the language of the question, briefly.
6. End with a sources section in exactly this format, one line per excerpt \
you used:
Sources:
[number] trust: high/medium/low, answers: directly/by implication
If you used no excerpt, write "Sources: none".

Example: for "What is my favourite colour?", if an excerpt says "my favourite \
colour is red", answer confidently that it's red. If the excerpts only mention \
liking red cars, red books and red computers, say my notes suggest red, \
without stating it as fact."""

# System prompts by version name; DEFAULT_PROMPT_VERSION is what answer() uses
# unless told otherwise.
PROMPTS = {"v1": _PROMPT_V1, "v2": _PROMPT_V2}
DEFAULT_PROMPT_VERSION = "v2"


@dataclass
class Answer:
    text: str
    sources: list[SearchResult]
    truncated: bool  # True if the prompt didn't fit in CONTEXT_WINDOW


def answer(
    question: str,
    k: int = 5,
    db_dir: str = DB_DIR,
    prompt_version: str = DEFAULT_PROMPT_VERSION,
    model: str = GENERATION_MODEL,
) -> Answer:
    """
    Retrieve the `k` chunks closest to `question`, ask `model` to answer from
    them using the system prompt PROMPTS[prompt_version], and return the
    answer together with those chunks.
    """
    sources = query_index(question, k, db_dir)
    response = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": PROMPTS[prompt_version]},
            {"role": "user", "content": _build_user_message(question, sources)},
        ],
        options={"temperature": 0, "num_ctx": CONTEXT_WINDOW},
    )
    return Answer(
        text=response["message"]["content"],
        sources=sources,
        truncated=response["prompt_eval_count"] >= CONTEXT_WINDOW,
    )


#### Private helpers ####

def _match_level(score: float) -> str:
    """Return "high", "medium" or "low" for a similarity score."""
    if score >= HIGH_MATCH:
        return "high"
    if score >= MEDIUM_MATCH:
        return "medium"
    return "low"


def _build_user_message(question: str, sources: list[SearchResult]) -> str:
    """
    Return the numbered excerpts (match level, note path, text), followed by
    the question.
    """
    parts = ["Excerpts from my notes:"]
    for number, result in enumerate(sources, start=1):
        parts.append(
            f"[{number}] ({_match_level(result.score)} match) {result.source}\n"
            f"{result.text}"
        )
    parts.append(f"Question: {question}")
    return "\n\n".join(parts)


#### Ask questions ####

if __name__ == "__main__":
    summary = build_index()
    print(
        f"Index: {summary['new']} new, {summary['edited']} edited, "
        f"{summary['deleted']} deleted, {summary['unchanged']} unchanged"
    )

    while True:
        question = input("\nQuestion (empty line to quit): ").strip()
        if not question:
            break

        result = answer(question)
        print("\nRetrieved from your notes:")
        for number, source in enumerate(result.sources, start=1):
            print(
                f"  [{number}] {source.score:.3f} ({_match_level(source.score)}) "
                f"{source.source}#{source.index}"
            )
        if result.truncated:
            print("\nWarning: the prompt was cut to fit the context window.")
        print(f"\nAnswer:\n{result.text}")

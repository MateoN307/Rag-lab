from dataclasses import dataclass

import ollama

from store import DB_DIR, SearchResult, build_index, query_index

GENERATION_MODEL = "llama3.2"

# A chunk whose score is at least HIGH_MATCH is a "high" match, at least
# MEDIUM_MATCH a "medium" match, and anything lower a "low" match.
HIGH_MATCH = 0.55
MEDIUM_MATCH = 0.50

SYSTEM_PROMPT = """\
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


@dataclass
class Answer:
    text: str
    sources: list[SearchResult]


def answer(question: str, k: int = 5, db_dir: str = DB_DIR) -> Answer:
    """
    Retrieve the `k` chunks closest to `question`, ask the local LLM to answer
    from them, and return the answer together with those chunks.
    """
    sources = query_index(question, k, db_dir)
    response = ollama.chat(
        model=GENERATION_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_message(question, sources)},
        ],
        options={"temperature": 0},
    )
    return Answer(text=response["message"]["content"], sources=sources)


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
        print(f"\nAnswer:\n{result.text}")

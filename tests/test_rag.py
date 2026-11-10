import pytest

import rag
from store import SearchResult


def result(source, score, text="some text", index=0):
    return SearchResult(text=text, source=source, index=index, score=score)


#### _match_level ####

MATCH_LEVEL_CASES = {
    "well_above_high": (0.63, "high"),
    "exactly_high": (0.55, "high"),
    "just_below_high": (0.549, "medium"),
    "exactly_medium": (0.50, "medium"),
    "just_below_medium": (0.499, "low"),
    "far_below": (0.30, "low"),
}


@pytest.mark.parametrize(
    "score, expected",
    MATCH_LEVEL_CASES.values(),
    ids=MATCH_LEVEL_CASES.keys(),
)
def test_match_level(score, expected):
    assert rag._match_level(score) == expected


#### _build_user_message ####


def test_build_user_message_numbers_and_labels_excerpts():
    """Each excerpt gets a number, its match level and its path; the question
    comes last."""
    message = rag._build_user_message(
        "Where is my trip?",
        [result("trip.md", 0.60, "Ferry at 9"), result("misc.md", 0.45, "Shopping list")],
    )

    assert message == (
        "Excerpts from my notes:\n\n"
        "[1] (high match) trip.md\nFerry at 9\n\n"
        "[2] (low match) misc.md\nShopping list\n\n"
        "Question: Where is my trip?"
    )


def test_build_user_message_without_excerpts():
    """An empty database still gives a well-formed message."""
    assert rag._build_user_message("Anything?", []) == (
        "Excerpts from my notes:\n\nQuestion: Anything?"
    )


#### answer ####


def test_answer_sends_rules_and_excerpts_and_returns_both(monkeypatch):
    """answer() sends the system rules plus the excerpts at temperature 0, and
    returns the model's text together with the chunks it was given."""
    found = [result("trip.md", 0.60, "Ferry at 9")]
    sent = {}

    def fake_query_index(question, k, db_dir):
        return found

    def fake_chat(model, messages, options):
        sent.update(model=model, messages=messages, options=options)
        return {"message": {"content": "The ferry is at 9."}}

    monkeypatch.setattr(rag, "query_index", fake_query_index)
    monkeypatch.setattr(rag.ollama, "chat", fake_chat)

    reply = rag.answer("When is the ferry?")

    assert reply.text == "The ferry is at 9."
    assert reply.sources == found
    assert sent["model"] == rag.GENERATION_MODEL
    assert sent["options"] == {"temperature": 0}
    assert sent["messages"][0] == {
        "role": "system",
        "content": rag.PROMPTS[rag.DEFAULT_PROMPT_VERSION],
    }
    assert sent["messages"][1]["content"].endswith("Question: When is the ferry?")

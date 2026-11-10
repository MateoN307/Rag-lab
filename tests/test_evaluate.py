import pytest

from evaluate import (
    answer_checks,
    answer_summary,
    first_rank,
    flagged,
    retrieval_summary,
)

#### first_rank ####

def test_first_rank_found():
    assert first_rank(["a.md", "b.md", "c.md"], ["c.md", "b.md"]) == 2


def test_first_rank_missing():
    assert first_rank(["a.md", "b.md"], ["z.md"]) is None


#### retrieval_summary ####

def test_retrieval_summary_hits_and_mrr():
    """Ranks 1, 4, 7 and missing: hit@5 = 2/4, hit@10 = 3/4,
    MRR = (1 + 1/4 + 1/7 + 0) / 4."""
    rows = [
        {"kind": "answerable", "rank": 1, "top_score": 0.6},
        {"kind": "answerable", "rank": 4, "top_score": 0.58},
        {"kind": "answerable", "rank": 7, "top_score": 0.55},
        {"kind": "answerable", "rank": None, "top_score": 0.5},
        {"kind": "unanswerable", "rank": None, "top_score": 0.45},
        {"kind": "unanswerable", "rank": None, "top_score": 0.43},
    ]
    summary = retrieval_summary(rows)

    assert summary["hit@5"] == 0.5
    assert summary["hit@10"] == 0.75
    assert summary["mrr"] == pytest.approx((1 + 1 / 4 + 1 / 7) / 4)
    assert summary["top_score_answerable"] == {"min": 0.5, "median": 0.565, "max": 0.6}
    assert summary["top_score_unanswerable"]["median"] == pytest.approx(0.44)


#### answer_checks ####

def test_answer_checks_answerable():
    text = "Book Modo and the ferry.\n\nSources:\n[1] trust: high, answers: directly"
    checks = answer_checks(text, "answerable", ["modo", "ferry", "hotel"])

    assert checks == {"facts_found": ["modo", "ferry"], "sources_format": True}


ADMIT_CASES = {
    "english_with_none": ("I couldn't find it in my notes.\n\nSources: none", True, True),
    "spanish_with_none": ("No encontré nada en mis notas.\n\nSources: none", True, True),
    "spanish_rule_four_sentence": (
        "Esta es lo que encontré, pero probablemente no sea lo que estás buscando.",
        True,
        False,
    ),
    "says_there_is_no_information": (
        "There's no information about the library hours in these excerpts.",
        True,
        False,
    ),
    "admits_but_lists_sources": ("I could not find it.\n\nSources:\n[2] trust: low", True, False),
    "answers_anyway": ("France won the 1998 World Cup.", False, False),
}


@pytest.mark.parametrize(
    "text, admitted, sources_none",
    ADMIT_CASES.values(),
    ids=ADMIT_CASES.keys(),
)
def test_answer_checks_unanswerable(text, admitted, sources_none):
    checks = answer_checks(text, "unanswerable", [])
    assert (checks["admitted"], checks["sources_none"]) == (admitted, sources_none)


def test_answer_checks_missing_sources_section():
    assert answer_checks("Just an answer.", "answerable", [])["sources_format"] is False


#### answer_summary and flagged ####

def test_answer_summary_and_flagged():
    rows = [
        {"id": "a", "kind": "answerable", "key_facts": ["x", "y"],
         "checks": {"facts_found": ["x", "y"], "sources_format": True}},
        {"id": "b", "kind": "answerable", "key_facts": ["z"],
         "checks": {"facts_found": [], "sources_format": False}},
        {"id": "c", "kind": "unanswerable", "key_facts": [],
         "checks": {"facts_found": [], "sources_format": True, "admitted": True, "sources_none": True}},
        {"id": "d", "kind": "unanswerable", "key_facts": [],
         "checks": {"facts_found": [], "sources_format": False, "admitted": False, "sources_none": False}},
    ]

    assert answer_summary(rows) == {
        "key_fact_recall": 2 / 3,
        "sources_format": 0.5,
        "unanswerable_admitted": 0.5,
        "unanswerable_sources_none": 0.5,
        "truncated": 0,
    }
    assert flagged(rows) == ["b", "d"]

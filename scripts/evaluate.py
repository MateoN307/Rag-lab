import argparse
import json
import os
import re
import statistics
import sys
from datetime import datetime

from dotenv import load_dotenv

APP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app")
sys.path.insert(0, APP_DIR)

from rag import DEFAULT_PROMPT_VERSION, GENERATION_MODEL, PROMPTS, answer
from store import DB_DIR, query_index

RETRIEVAL_DEPTH = 10  # results fetched per question for hit@5, hit@10 and MRR

ADMIT_PHRASES = [
    "couldn't find",
    "could not find",
    "not in my notes",
    "no encontré",
    "no pude encontrar",
    "probablemente no sea lo que",
    "no information",
    "no direct mention",
    "nothing directly related",
]
_SOURCES_SECTION = re.compile(r"sources:\s*(none\b|\n\s*\[\d+\])", re.IGNORECASE)
_SOURCES_NONE = re.compile(r"sources:\s*none\b", re.IGNORECASE)


def first_rank(retrieved_sources: list[str], expected_sources: list[str]) -> int | None:
    """Return the 1-based rank of the first retrieved source that is expected,
    or None if none of them is."""
    for rank, source in enumerate(retrieved_sources, start=1):
        if source in expected_sources:
            return rank
    return None


def retrieval_summary(rows: list[dict]) -> dict:
    """Return hit@5, hit@10 and MRR over the answerable rows, and the top-score
    spread (min, median, max) for answerable and unanswerable rows."""
    answerable = [r for r in rows if r["kind"] == "answerable"]
    ranks = [r["rank"] for r in answerable]
    summary = {
        "hit@5": sum(1 for rank in ranks if rank is not None and rank <= 5) / len(ranks),
        "hit@10": sum(1 for rank in ranks if rank is not None) / len(ranks),
        "mrr": sum(1 / rank for rank in ranks if rank is not None) / len(ranks),
    }
    for kind in ("answerable", "unanswerable"):
        scores = [r["top_score"] for r in rows if r["kind"] == kind]
        summary[f"top_score_{kind}"] = {
            "min": min(scores),
            "median": statistics.median(scores),
            "max": max(scores),
        }
    return summary


def answer_checks(text: str, kind: str, key_facts: list[str]) -> dict:
    """Return the checks for one answer: which key facts are present, whether a
    Sources section is well formed, and (unanswerable only) whether it admitted
    not finding the answer and wrote "Sources: none"."""
    lowered = text.lower()
    checks = {
        "facts_found": [fact for fact in key_facts if fact.lower() in lowered],
        "sources_format": bool(_SOURCES_SECTION.search(text)),
    }
    if kind == "unanswerable":
        checks["admitted"] = any(phrase in lowered for phrase in ADMIT_PHRASES)
        checks["sources_none"] = bool(_SOURCES_NONE.search(text))
    return checks


def answer_summary(rows: list[dict]) -> dict:
    """Return key-fact recall over answerable rows, the share of answers with a
    well-formed Sources section, and admitted / "Sources: none" rates over
    unanswerable rows."""
    answerable = [r for r in rows if r["kind"] == "answerable"]
    unanswerable = [r for r in rows if r["kind"] == "unanswerable"]
    total_facts = sum(len(r["key_facts"]) for r in answerable)
    found_facts = sum(len(r["checks"]["facts_found"]) for r in answerable)
    return {
        "key_fact_recall": found_facts / total_facts,
        "sources_format": sum(r["checks"]["sources_format"] for r in rows) / len(rows),
        "unanswerable_admitted": sum(r["checks"]["admitted"] for r in unanswerable) / len(unanswerable),
        "unanswerable_sources_none": sum(r["checks"]["sources_none"] for r in unanswerable) / len(unanswerable),
    }


def flagged(rows: list[dict]) -> list[str]:
    """Return the ids of answers to review by hand: answerable ones missing a
    key fact, and unanswerable ones that didn't admit it."""
    ids = []
    for r in rows:
        if r["kind"] == "answerable" and len(r["checks"]["facts_found"]) < len(r["key_facts"]):
            ids.append(r["id"])
        if r["kind"] == "unanswerable" and not r["checks"]["admitted"]:
            ids.append(r["id"])
    return ids


#### Running an evaluation ####

def run_retrieval(questions: list[dict], db_dir: str) -> list[dict]:
    rows = []
    for q in questions:
        results = query_index(q["question"], RETRIEVAL_DEPTH, db_dir)
        retrieved = [r.source for r in results]
        rows.append({
            "id": q["id"],
            "kind": q["kind"],
            "retrieved": [[r.source, r.index, round(r.score, 4)] for r in results],
            "rank": first_rank(retrieved, q["sources"]) if q["kind"] == "answerable" else None,
            "top_score": results[0].score if results else 0.0,
        })
    return rows


def run_answers(questions: list[dict], args) -> list[dict]:
    rows = []
    for number, q in enumerate(questions, start=1):
        print(f"  answering {number}/{len(questions)}: {q['id']}", flush=True)
        reply = answer(q["question"], args.k, args.db_dir, args.prompt, args.model)
        rows.append({
            "id": q["id"],
            "kind": q["kind"],
            "key_facts": q["key_facts"],
            "answer": reply.text,
            "checks": answer_checks(reply.text, q["kind"], q["key_facts"]),
        })
    return rows


def print_scorecard(name: str, retrieval: dict, answers: dict | None, review: list[str]) -> None:
    print(f"\n=== {name} ===")
    print(f"Retrieval: hit@5 {retrieval['hit@5']:.0%}  hit@10 {retrieval['hit@10']:.0%}  MRR {retrieval['mrr']:.3f}")
    for kind in ("answerable", "unanswerable"):
        spread = retrieval[f"top_score_{kind}"]
        print(f"  top score, {kind:12}: min {spread['min']:.3f}  median {spread['median']:.3f}  max {spread['max']:.3f}")
    if answers is not None:
        print(
            f"Answers:   key facts {answers['key_fact_recall']:.0%}  sources format {answers['sources_format']:.0%}  "
            f"unanswerable admitted {answers['unanswerable_admitted']:.0%}  "
            f"'Sources: none' {answers['unanswerable_sources_none']:.0%}"
        )
        print(f"  review by hand: {', '.join(review) if review else 'nothing flagged'}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Score the RAG pipeline against the evaluation set.")
    parser.add_argument("--name", required=True, help="configuration name, used in the results file name")
    parser.add_argument("--prompt", default=DEFAULT_PROMPT_VERSION, choices=sorted(PROMPTS))
    parser.add_argument("--model", default=GENERATION_MODEL)
    parser.add_argument("--k", type=int, default=5, help="chunks given to the model when answering")
    parser.add_argument("--db-dir", default=DB_DIR)
    parser.add_argument("--answers", action="store_true", help="also run the (slow) answer phase")
    args = parser.parse_args()

    load_dotenv(os.path.join(APP_DIR, "..", ".env"))
    eval_path = os.environ.get("EVAL_PATH")
    if not eval_path:
        sys.exit("EVAL_PATH is not set; add it to .env")
    with open(eval_path, encoding="utf-8") as f:
        questions = json.load(f)

    retrieval_rows = run_retrieval(questions, args.db_dir)
    retrieval = retrieval_summary(retrieval_rows)
    answer_rows = run_answers(questions, args) if args.answers else None
    answers = answer_summary(answer_rows) if answer_rows else None
    review = flagged(answer_rows) if answer_rows else []

    print_scorecard(args.name, retrieval, answers, review)

    results_dir = os.path.join(os.path.dirname(eval_path), "results")
    os.makedirs(results_dir, exist_ok=True)
    out = os.path.join(results_dir, f"{datetime.now():%Y-%m-%d_%H%M}_{args.name}.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(
            {
                "config": vars(args),
                "retrieval": retrieval,
                "answers": answers,
                "review": review,
                "retrieval_rows": retrieval_rows,
                "answer_rows": answer_rows,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    print(f"\nFull results: {out}")


if __name__ == "__main__":
    main()

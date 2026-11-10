import hashlib
import os
from dataclasses import dataclass

import chromadb
import ollama
from dotenv import load_dotenv

from chunker import CHUNK_WORDS, chunk_file, find_md_files
from embedder import embed_text

load_dotenv()

APP_DIR = os.path.dirname(os.path.abspath(__file__))
# Database folder: DB_DIR from .env (one database per vault), else app/db.
DB_DIR = os.environ.get("DB_DIR") or os.path.join(APP_DIR, "db")
COLLECTION_NAME = "vault_chunks"

# When the model rejects a chunk as too long, the note is re-chunked with
# chunk_words * SHRINK_FACTOR, down to MIN_CHUNK_WORDS.
SHRINK_FACTOR = 0.75
MIN_CHUNK_WORDS = 20

VAULT_PATH = os.environ.get("VAULT_PATH")
# Folders (relative to the vault) left out of the index, separated by ";".
SKIP_FOLDERS = [f for f in os.environ.get("SKIP_FOLDERS", "").split(";") if f.strip()]


@dataclass
class SearchResult:
    text: str
    source: str
    index: int
    score: float


def build_index(
    vault_path: str = VAULT_PATH, db_dir: str = DB_DIR, skip: list[str] = SKIP_FOLDERS
) -> dict:
    """
    Bring the database at `db_dir` in line with the notes in `vault_path`
    (except those inside the folders in `skip`):
    store new notes, re-store edited ones, remove deleted ones, and skip
    unchanged ones (compared by each note's fingerprint).

    Return a summary: counts of "new", "edited", "deleted" and "unchanged"
    notes; "empty" and "too_dense", the sorted paths of notes that produced
    no chunks or couldn't fit the model even at MIN_CHUNK_WORDS; and
    "shrunk", {path: chunk_words} for notes stored with smaller chunks.
    """
    if not vault_path:
        raise ValueError("VAULT_PATH is not set; add it to .env")

    on_disk = _disk_hashes(vault_path, find_md_files(vault_path, skip))
    collection = _open_collection(db_dir)
    in_store = _db_hashes(collection)

    summary = {
        "new": 0,
        "edited": 0,
        "deleted": 0,
        "unchanged": 0,
        "empty": [],
        "shrunk": {},
        "too_dense": [],
    }
    for source in sorted(on_disk.keys() | in_store.keys()):
        disk_hash = on_disk.get(source)
        stored_hash = in_store.get(source)

        if disk_hash is None:
            # Only in the database: the note was deleted from the vault.
            collection.delete(where={"source": source})
            summary["deleted"] += 1
            continue
        if disk_hash == stored_hash:
            summary["unchanged"] += 1
            continue
        if stored_hash is None:
            bucket = "new"
        else:
            # Edited: old chunks must go first, since add() ignores ids that
            # already exist.
            collection.delete(where={"source": source})
            bucket = "edited"

        outcome, chunk_words = _add_note(collection, vault_path, source, disk_hash)
        if outcome == "stored":
            summary[bucket] += 1
            if chunk_words < CHUNK_WORDS:
                summary["shrunk"][source] = chunk_words
        else:
            # "empty" or "too_dense": nothing was stored for this note.
            summary[outcome].append(source)

    return summary


def query_index(question: str, k: int = 5, db_dir: str = DB_DIR) -> list[SearchResult]:
    """
    Embed `question` and return the `k` stored chunks closest to it, best
    first, each with its text, source, index and cosine similarity score.
    """
    collection = _open_collection(db_dir)
    response = collection.query(
        query_embeddings=[embed_text(question)],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )

    # Each field is a list of lists: one inner list per query embedding, and
    # we sent one, so [0]. Position i in the inner lists is the i-th result.
    results = []
    for text, metadata, distance in zip(
        response["documents"][0], response["metadatas"][0], response["distances"][0]
    ):
        results.append(
            SearchResult(
                text=text,
                source=metadata["source"],
                index=metadata["index"],
                score=1 - distance,
            )
        )
    return results


#### Private helpers ####

def _hash_file(path: str) -> str:
    """Return the sha256 fingerprint (hex string) of the file's raw bytes."""
    with open(path, "rb") as f:
        data = f.read()
    return hashlib.sha256(data).hexdigest()


def _disk_hashes(vault_path: str, sources: list[str]) -> dict[str, str]:
    """
    Return {source: fingerprint} with one entry per note in `sources`, where
    each source is a path relative to `vault_path` (e.g. "plans/trip.md").
    """
    hashes = {}
    for source in sources:
        hashes[source] = _hash_file(os.path.join(vault_path, source))
    return hashes


def _db_hashes(collection) -> dict[str, str]:
    """
    Return {source: fingerprint} with one entry per note stored in
    `collection`, read from its chunks' metadata.
    """
    metadatas = collection.get(include=["metadatas"])["metadatas"]
    hashes = {}
    for metadata in metadatas:
        # Every chunk of a note has the same source and hash, so repeated
        # entries just overwrite the key with the same value.
        hashes[metadata["source"]] = metadata["hash"]
    return hashes


def _add_note(
    collection, vault_path: str, source: str, note_hash: str
) -> tuple[str, int]:
    """
    Chunk and embed the note at `source` (relative to `vault_path`) and store
    all its chunks in one add, each with {source, index, hash} metadata. If
    the model rejects a chunk as too long, re-chunk the whole note with
    chunk_words * SHRINK_FACTOR and retry, down to MIN_CHUNK_WORDS.

    Return (outcome, chunk_words): outcome is "stored", "empty" (no chunks)
    or "too_dense" (didn't fit even at MIN_CHUNK_WORDS; nothing stored).
    """
    file_path = os.path.join(vault_path, source)
    chunk_words = CHUNK_WORDS
    while True:
        chunks = chunk_file(file_path, source, chunk_words)
        if not chunks:
            return "empty", chunk_words

        embeddings = _embed_all([chunk.text for chunk in chunks])
        if embeddings is not None:
            break
        if chunk_words <= MIN_CHUNK_WORDS:
            return "too_dense", chunk_words
        chunk_words = max(MIN_CHUNK_WORDS, round(chunk_words * SHRINK_FACTOR))

    collection.add(
        ids=[f"{chunk.source}#{chunk.index}" for chunk in chunks],
        embeddings=embeddings,
        documents=[chunk.text for chunk in chunks],
        metadatas=[
            {"source": chunk.source, "index": chunk.index, "hash": note_hash}
            for chunk in chunks
        ],
    )
    return "stored", chunk_words


def _embed_all(texts: list[str]) -> list[list[float]] | None:
    """
    Embed every text, in order. Return None if the model rejects one for
    exceeding its context length; any other error is raised as usual.
    """
    embeddings = []
    for text in texts:
        try:
            embeddings.append(embed_text(text))
        except ollama.ResponseError as error:
            if error.status_code == 400 and "context length" in str(error):
                return None
            raise
    return embeddings


def _open_collection(db_dir: str):
    """
    Open the persistent database at `db_dir` (created if missing) and return
    its chunk collection, which compares vectors by cosine distance.
    """
    client = chromadb.PersistentClient(path=db_dir)
    return client.get_or_create_collection(
        COLLECTION_NAME,
        configuration={"hnsw": {"space": "cosine"}},
    )


#### Debug tool ####

if __name__ == "__main__":
    summary = build_index()
    print(
        f"Index: {summary['new']} new, {summary['edited']} edited, "
        f"{summary['deleted']} deleted, {summary['unchanged']} unchanged, "
        f"{len(summary['empty'])} empty"
    )
    if summary["shrunk"]:
        print(f"Stored with smaller chunks: {summary['shrunk']}")
    if summary["too_dense"]:
        print(f"Too dense to store: {summary['too_dense']}")

    try:
        while True:
            question = input("\nQuestion (empty line to quit): ").strip()
            if not question:
                break
            for result in query_index(question):
                print(f"{result.score:.3f}  {result.source}#{result.index}")
                print(f"       {result.text[:100]!r}")
    except (KeyboardInterrupt, EOFError):
        print("\nBye.")

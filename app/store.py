import os
import hashlib

import chromadb
from dotenv import load_dotenv

from chunker import chunk_file
from embedder import embed_text

load_dotenv()

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(APP_DIR, "db")
COLLECTION_NAME = "vault_chunks"

VAULT_PATH = os.environ.get("VAULT_PATH")


def build_index() -> None:
    """
    Ensure the persistent vector index exists and is populated:
    chunk the vault, embed each chunk, and store it with enough
    metadata to identify it later. Should be safe to call repeatedly
    without duplicating work (i.e. don't re-embed everything every run).
    """
    pass


def query_index(question: str, k: int = 5) -> list:
    """
    Embed `question`, retrieve the top-k most similar stored chunks,
    and return them — each result needs to carry at least: the chunk
    text, its source/position metadata, and a similarity score.
    """
    pass


#### Private helpers ####


#### Tests ####


if __name__ == "__main__":
    pass

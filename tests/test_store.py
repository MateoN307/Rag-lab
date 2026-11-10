import hashlib

import ollama
import pytest

import store
from embedder import cosine_similarity
from store import _db_hashes, _disk_hashes, _hash_file, _open_collection


def sha256_of(data: bytes) -> str:
    """Expected fingerprint, computed independently of the code under test."""
    return hashlib.sha256(data).hexdigest()


#### _hash_file ####


def test_hash_file_known_answer(tmp_path):
    """A file containing exactly b"hello" has a known sha256."""
    path = tmp_path / "note.md"
    path.write_bytes(b"hello")

    assert _hash_file(str(path)) == (
        "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
    )


def test_hash_file_changes_and_restores(tmp_path):
    """Editing a file changes its hash; undoing the edit brings it back."""
    path = tmp_path / "note.md"
    path.write_bytes(b"first version")
    original = _hash_file(str(path))

    path.write_bytes(b"first version, edited")
    assert _hash_file(str(path)) != original

    path.write_bytes(b"first version")
    assert _hash_file(str(path)) == original


def test_hash_file_reads_raw_bytes(tmp_path):
    """Files that differ only in line endings must hash differently."""
    windows = tmp_path / "windows.md"
    unix = tmp_path / "unix.md"
    windows.write_bytes(b"a\r\nb")
    unix.write_bytes(b"a\nb")

    assert _hash_file(str(windows)) != _hash_file(str(unix))


def test_hash_file_same_content_different_files(tmp_path):
    """The hash depends on the bytes only, not the file's name or folder."""
    first = tmp_path / "one.md"
    (tmp_path / "sub").mkdir()
    second = tmp_path / "sub" / "two.md"
    first.write_bytes(b"same text")
    second.write_bytes(b"same text")

    assert _hash_file(str(first)) == _hash_file(str(second))


def test_hash_file_missing_file(tmp_path):
    """A path that doesn't exist raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        _hash_file(str(tmp_path / "does_not_exist.md"))


#### _disk_hashes ####


def test_disk_hashes_keys_and_own_hashes(tmp_path):
    """Keys are the relative sources unchanged; each gets its own file's hash."""
    (tmp_path / "a.md").write_bytes(b"alpha")
    (tmp_path / "b.md").write_bytes(b"beta")

    assert _disk_hashes(str(tmp_path), ["a.md", "b.md"]) == {
        "a.md": sha256_of(b"alpha"),
        "b.md": sha256_of(b"beta"),
    }


def test_disk_hashes_nested_source(tmp_path):
    """A source inside a subfolder is opened via the vault path."""
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "a.md").write_bytes(b"nested")

    assert _disk_hashes(str(tmp_path), ["sub/a.md"]) == {
        "sub/a.md": sha256_of(b"nested"),
    }


def test_disk_hashes_empty_list(tmp_path):
    """No sources gives an empty dict."""
    assert _disk_hashes(str(tmp_path), []) == {}


#### _open_collection ####


def test_open_collection_uses_cosine(tmp_path):
    """The collection compares vectors by cosine distance."""
    collection = _open_collection(str(tmp_path / "db"))
    assert collection.configuration["hnsw"]["space"] == "cosine"


def test_open_collection_keeps_data_between_opens(tmp_path):
    """Opening the same folder again gives back what was stored."""
    db_dir = str(tmp_path / "db")
    _open_collection(db_dir).add(
        ids=["a.md#0"],
        embeddings=[[1.0, 0.0]],
        documents=["text"],
        metadatas=[{"source": "a.md", "index": 0, "hash": "h1"}],
    )
    assert _open_collection(db_dir).get()["ids"] == ["a.md#0"]


#### _db_hashes ####


def add_fake_chunks(collection, chunks):
    """Store (source, index, hash) entries with tiny made-up vectors."""
    collection.add(
        ids=[f"{source}#{index}" for source, index, _ in chunks],
        embeddings=[[1.0, float(i)] for i in range(len(chunks))],
        documents=["text"] * len(chunks),
        metadatas=[
            {"source": source, "index": index, "hash": hash_}
            for source, index, hash_ in chunks
        ],
    )


def test_db_hashes_one_entry_per_note(tmp_path):
    """A note stored as several chunks appears once, with its hash."""
    collection = _open_collection(str(tmp_path / "db"))
    add_fake_chunks(
        collection,
        [
            ("cats.md", 0, "h_cats"),
            ("plans/trip.md", 0, "h_trip"),
            ("plans/trip.md", 1, "h_trip"),
        ],
    )
    assert _db_hashes(collection) == {"cats.md": "h_cats", "plans/trip.md": "h_trip"}


def test_db_hashes_empty_collection(tmp_path):
    """Nothing stored gives an empty dict."""
    assert _db_hashes(_open_collection(str(tmp_path / "db"))) == {}


#### build_index and query_index ####
# These use a fake embed_text so they run instantly and never call Ollama.
# store.py does `from embedder import embed_text`, which makes its own name
# for the function, so the fake must replace store.embed_text specifically.

CONTEXT_ERROR = "the input length exceeds the context length"


def fake_vector(text):
    """A tiny 2-number vector: how much the text is about apples vs cars."""
    return [text.count("apple") + 0.1, text.count("car") + 0.1]


@pytest.fixture
def fake_embed(monkeypatch):
    """Replace the store's embed_text with fake_vector for one test."""
    monkeypatch.setattr(store, "embed_text", fake_vector)


@pytest.fixture
def vault(tmp_path):
    """An empty vault folder; tests add notes with write_note()."""
    folder = tmp_path / "vault"
    folder.mkdir()
    return folder


@pytest.fixture
def db_dir(tmp_path):
    return str(tmp_path / "db")


def write_note(vault, name, text):
    (vault / name).write_text(text, encoding="utf-8")


def stored_texts(db_dir, source):
    collection = _open_collection(db_dir)
    return collection.get(where={"source": source}, include=["documents"])["documents"]


def test_build_index_new_then_unchanged(fake_embed, vault, db_dir):
    """A first run stores every note; a second run with no changes does nothing."""
    write_note(vault, "a.md", "apple pie")
    write_note(vault, "b.md", "fast car")

    first = store.build_index(str(vault), db_dir)
    second = store.build_index(str(vault), db_dir)

    assert (first["new"], first["unchanged"]) == (2, 0)
    assert (second["new"], second["edited"], second["deleted"], second["unchanged"]) == (0, 0, 0, 2)


def test_build_index_edited_note(fake_embed, vault, db_dir):
    """An edited note is re-stored, and its old text is gone."""
    write_note(vault, "a.md", "old apple text")
    store.build_index(str(vault), db_dir)

    write_note(vault, "a.md", "new apple text")
    summary = store.build_index(str(vault), db_dir)

    assert summary["edited"] == 1
    assert stored_texts(db_dir, "a.md") == ["new apple text"]


def test_build_index_deleted_note(fake_embed, vault, db_dir):
    """A note removed from the vault has its chunks removed from the database."""
    write_note(vault, "a.md", "apple")
    write_note(vault, "b.md", "car")
    store.build_index(str(vault), db_dir)

    (vault / "b.md").unlink()
    summary = store.build_index(str(vault), db_dir)

    assert summary["deleted"] == 1
    assert stored_texts(db_dir, "b.md") == []
    assert stored_texts(db_dir, "a.md") == ["apple"]


def test_build_index_empty_note(fake_embed, vault, db_dir):
    """A note with no chunks is listed only under "empty"."""
    write_note(vault, "empty.md", "---\ntags: [x]\n---\n")
    summary = store.build_index(str(vault), db_dir)

    assert summary["empty"] == ["empty.md"]
    assert summary["new"] == 0


def test_build_index_shrinks_oversized_note(monkeypatch, vault, db_dir):
    """If the model rejects chunks over 400 words, the note is re-chunked at 338."""

    def rejects_long_texts(text):
        if len(text.split()) > 400:
            raise ollama.ResponseError(CONTEXT_ERROR, 400)
        return [1.0, 1.0]

    monkeypatch.setattr(store, "embed_text", rejects_long_texts)
    write_note(vault, "long.md", " ".join(f"word{i}" for i in range(1000)))
    summary = store.build_index(str(vault), db_dir)

    assert summary["new"] == 1
    assert summary["shrunk"] == {"long.md": 338}
    assert max(len(t.split()) for t in stored_texts(db_dir, "long.md")) == 338


def test_build_index_too_dense_note(monkeypatch, vault, db_dir):
    """If no chunk size fits, the note is listed under "too_dense" and not stored."""

    def rejects_everything(text):
        raise ollama.ResponseError(CONTEXT_ERROR, 400)

    monkeypatch.setattr(store, "embed_text", rejects_everything)
    write_note(vault, "dense.md", "some text")
    summary = store.build_index(str(vault), db_dir)

    assert summary["too_dense"] == ["dense.md"]
    assert summary["new"] == 0
    assert stored_texts(db_dir, "dense.md") == []


def test_build_index_other_errors_are_raised(monkeypatch, vault, db_dir):
    """Any Ollama error other than the context-length one stops the build."""

    def model_missing(text):
        raise ollama.ResponseError("model not found", 404)

    monkeypatch.setattr(store, "embed_text", model_missing)
    write_note(vault, "a.md", "apple")

    with pytest.raises(ollama.ResponseError, match="model not found"):
        store.build_index(str(vault), db_dir)


def test_build_index_requires_vault_path(db_dir):
    """A missing vault path (VAULT_PATH not set) raises a clear error."""
    with pytest.raises(ValueError, match="VAULT_PATH is not set"):
        store.build_index(None, db_dir)


def test_query_index_ranks_best_first(fake_embed, vault, db_dir):
    """Results come back best first, with score = cosine similarity."""
    write_note(vault, "apples.md", "apple apple apple")
    write_note(vault, "cars.md", "car car car")
    store.build_index(str(vault), db_dir)

    results = store.query_index("apple", k=2, db_dir=db_dir)

    assert [r.source for r in results] == ["apples.md", "cars.md"]
    assert results[0].score == pytest.approx(
        cosine_similarity(fake_vector("apple"), fake_vector("apple apple apple"))
    )
    assert results[0].score > results[1].score

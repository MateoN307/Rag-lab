import hashlib

import pytest

from store import _hash_file, _hash_notes


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


#### _hash_notes ####


def test_hash_notes_keys_and_own_hashes(tmp_path):
    """Keys are the relative sources unchanged; each gets its own file's hash."""
    (tmp_path / "a.md").write_bytes(b"alpha")
    (tmp_path / "b.md").write_bytes(b"beta")

    assert _hash_notes(str(tmp_path), ["a.md", "b.md"]) == {
        "a.md": sha256_of(b"alpha"),
        "b.md": sha256_of(b"beta"),
    }


def test_hash_notes_nested_source(tmp_path):
    """A source inside a subfolder is opened via the vault path."""
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "a.md").write_bytes(b"nested")

    assert _hash_notes(str(tmp_path), ["sub/a.md"]) == {
        "sub/a.md": sha256_of(b"nested"),
    }


def test_hash_notes_empty_list(tmp_path):
    """No sources gives an empty dict."""
    assert _hash_notes(str(tmp_path), []) == {}

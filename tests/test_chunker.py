import os

import pytest

from chunker import (
    Chunk,
    _md_files_in_folder,
    _md_parser,
    chunk_dir,
    chunk_file,
    find_md_files,
)

# Fixture folders live next to this file, so paths are computed relative to
# it (no machine-specific paths, works wherever the repo is cloned).
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
CHUNK_FILE_TEST_DIR = os.path.join(TESTS_DIR, "chunker", "3")
CHUNK_DIR_TEST_DIR = os.path.join(TESTS_DIR, "chunker", "4")


#### chunk_file ####

# Edge cases: file shorter than one chunk, file spanning multiple chunks
# (overlap correctness), empty/header-only file, and files ending inside /
# exactly at / just past the first chunk (no duplicate tail chunk made only
# of overlap words).
CHUNK_FILE_CASES = {
    "short.md": [
        Chunk(text="one two three four five", source="short.md", index=0),
    ],
    "header_only.md": [],
    "empty.md": [],
    "multi_chunk.md": [
        Chunk(
            text=" ".join(f"word{i}" for i in range(1, 451)),
            source="multi_chunk.md",
            index=0,
        ),
        Chunk(
            text=" ".join(f"word{i}" for i in range(401, 851)),
            source="multi_chunk.md",
            index=1,
        ),
        Chunk(
            text=" ".join(f"word{i}" for i in range(801, 1001)),
            source="multi_chunk.md",
            index=2,
        ),
    ],
    "overlap_420.md": [
        Chunk(
            text=" ".join(f"word{i}" for i in range(1, 421)),
            source="overlap_420.md",
            index=0,
        ),
    ],
    "exact_450.md": [
        Chunk(
            text=" ".join(f"word{i}" for i in range(1, 451)),
            source="exact_450.md",
            index=0,
        ),
    ],
    "one_over_451.md": [
        Chunk(
            text=" ".join(f"word{i}" for i in range(1, 451)),
            source="one_over_451.md",
            index=0,
        ),
        Chunk(
            text=" ".join(f"word{i}" for i in range(401, 452)),
            source="one_over_451.md",
            index=1,
        ),
    ],
    "over_461.md": [
        Chunk(
            text=" ".join(f"word{i}" for i in range(1, 451)),
            source="over_461.md",
            index=0,
        ),
        Chunk(
            text=" ".join(f"word{i}" for i in range(401, 462)),
            source="over_461.md",
            index=1,
        ),
    ],
}


@pytest.mark.parametrize(
    "filename, expected",
    CHUNK_FILE_CASES.items(),
    ids=CHUNK_FILE_CASES.keys(),
)
def test_chunk_file(filename, expected):
    file_path = os.path.join(CHUNK_FILE_TEST_DIR, filename)
    assert chunk_file(file_path, filename) == expected


#### _md_parser ####

# Edge cases: note with frontmatter, without frontmatter, with a body "---"
# divider but no frontmatter, with frontmatter AND a body divider,
# frontmatter only, empty, plain wiki link ([[Note Name]]), wiki link with
# display text ([[Note Name|Display]]), image embed (![[...]]), and every
# link/embed form plus frontmatter in one note.
# Each case is (raw markdown, expected cleaned text). The raw markdown is
# written one line per string piece so every newline is visible; Python
# joins adjacent string literals into one string.
MD_PARSER_CASES = {
    "with_frontmatter": (
        (
            "---\n"
            "tags: [test, fixture]\n"
            "status: draft\n"
            "---\n"
            "\n"
            "# Sample note\n"
            "\n"
            "This is a note that has frontmatter and nothing else unusual in its body.\n"
        ),
        (
            "# Sample note This is a note that has frontmatter and nothing "
            "else unusual in its body."
        ),
    ),
    "no_frontmatter": (
        (
            "# Sample note\n"
            "\n"
            "This is a note that has no frontmatter at all — it just starts with content.\n"
        ),
        (
            "# Sample note This is a note that has no frontmatter at all — "
            "it just starts with content."
        ),
    ),
    "no_frontmatter_with_divider": (
        (
            "# Sample note\n"
            "\n"
            "This note has no frontmatter, but uses a horizontal rule divider below.\n"
            "\n"
            "---\n"
            "\n"
            "This text comes after the divider and should NOT be removed.\n"
        ),
        (
            "# Sample note This note has no frontmatter, but uses a "
            "horizontal rule divider below. --- This text comes after the "
            "divider and should NOT be removed."
        ),
    ),
    "frontmatter_with_divider": (
        (
            "---\n"
            "tags: [test, fixture]\n"
            "status: draft\n"
            "---\n"
            "\n"
            "# Sample note\n"
            "\n"
            "This note has frontmatter, and also a horizontal rule divider further down.\n"
            "\n"
            "---\n"
            "\n"
            "This text comes after the divider and should NOT be removed.\n"
        ),
        (
            "# Sample note This note has frontmatter, and also a horizontal "
            "rule divider further down. --- This text comes after the "
            "divider and should NOT be removed."
        ),
    ),
    "frontmatter_only": (
        (
            "---\n"
            "tags: [test, fixture]\n"
            "status: draft\n"
            "---\n"
        ),
        "",
    ),
    "empty": (
        "",
        "",
    ),
    "wiki_link_plain": (
        "[[Note Name]] is referenced here.\n",
        "Note Name is referenced here.",
    ),
    "wiki_link_display": (
        "[[Note Name|Display Text]] is referenced here.\n",
        "Display Text is referenced here.",
    ),
    "image_embed": (
        "Here is an image: ![[diagram.png]] and more text.\n",
        "Here is an image: and more text.",
    ),
    "mixed_links_embeds": (
        (
            "---\n"
            "tags: [test]\n"
            "---\n"
            "\n"
            "See [[Project Plan]] for details, also check [[Project Plan|the plan]] "
            "and the diagram ![[diagram.png]] below.\n"
        ),
        (
            "See Project Plan for details, also check the plan and the "
            "diagram below."
        ),
    ),
}


@pytest.mark.parametrize(
    "text, expected",
    MD_PARSER_CASES.values(),
    ids=MD_PARSER_CASES.keys(),
)
def test_md_parser(text, expected):
    assert _md_parser(text) == expected


#### chunk_dir ####


def test_chunk_dir_walks_nested_folders():
    """Nested subfolders get walked, and chunks from several files are
    concatenated with consistent per-file indexing."""
    expected = [
        Chunk(text="one two three four five", source="short.md", index=0),
        Chunk(
            text=" ".join(f"word{i}" for i in range(1, 451)),
            source=os.path.join("sub_a", "multi_chunk.md"),
            index=0,
        ),
        Chunk(
            text=" ".join(f"word{i}" for i in range(401, 851)),
            source=os.path.join("sub_a", "multi_chunk.md"),
            index=1,
        ),
        Chunk(
            text=" ".join(f"word{i}" for i in range(801, 1001)),
            source=os.path.join("sub_a", "multi_chunk.md"),
            index=2,
        ),
        Chunk(
            text=(
                "# Sample note This is a note that has frontmatter and "
                "nothing else unusual in its body."
            ),
            source=os.path.join("sub_a", "sub_b", "with_frontmatter.md"),
            index=0,
        ),
    ]

    result = chunk_dir(CHUNK_DIR_TEST_DIR)

    # os.walk / os.listdir return entries in arbitrary (filesystem) order, so
    # put both lists in the same order before comparing.
    def sort_key(c):
        return (c.source, c.index)

    assert sorted(result, key=sort_key) == sorted(expected, key=sort_key)


def test_chunk_dir_rejects_missing_folder():
    """A path that doesn't exist raises ValueError."""
    missing = os.path.join(CHUNK_DIR_TEST_DIR, "does_not_exist")
    with pytest.raises(ValueError):
        chunk_dir(missing)


def test_chunk_dir_empty_folder(tmp_path):
    """An existing but empty folder is fine: no chunks, no error."""
    assert chunk_dir(str(tmp_path)) == []


#### _md_files_in_folder ####

# Each case is (files to create, folders to create, expected .md names).
# Everything is built inside tmp_path, a fresh empty folder per test, because
# _md_files_in_folder only looks at names and file/folder types, never contents.
# Folders are created first, so a file can live inside one ("sub1/c.md").
MD_FILES_IN_FOLDER_CASES = {
    "empty": ([], [], []),
    "only_dirs": ([], ["sub1", "sub2"], []),
    "dirs_and_other_files": (["image.png", "notes.txt"], ["sub1"], []),
    "only_md": (["a.md", "b.md"], [], ["a.md", "b.md"]),
    "mixed": (["a.md", "b.md", "notes.txt"], ["sub1"], ["a.md", "b.md"]),
    "md_in_subfolder": (["sub1/c.md"], ["sub1"], []),
}


@pytest.mark.parametrize(
    "files, dirs, expected",
    MD_FILES_IN_FOLDER_CASES.values(),
    ids=MD_FILES_IN_FOLDER_CASES.keys(),
)
def test_md_files_in_folder(files, dirs, expected, tmp_path):
    for name in dirs:
        (tmp_path / name).mkdir()
    for name in files:
        (tmp_path / name).write_text("")

    result = _md_files_in_folder(str(tmp_path))

    # _md_files_in_folder returns full paths (folder + name), and os.listdir gives
    # entries in arbitrary order, so build the full expected paths and put
    # both lists in the same order before comparing.
    expected_paths = [os.path.join(str(tmp_path), name) for name in expected]
    assert sorted(result) == sorted(expected_paths)


#### find_md_files ####

# Each case is (folders to create, files to create, expected relative paths).
# Built in tmp_path. Folders are listed parent-first so each one can be
# created inside the previous. What's tested here is walking into folders and
# the relative paths; which file types count is _md_files_in_folder's test.
FIND_MD_FILES_CASES = {
    "depth_0": ([], ["a.md"], ["a.md"]),
    "depth_1": (["l1"], ["l1/a.md"], ["l1/a.md"]),
    "depth_2": (["l1", "l1/l2"], ["l1/l2/a.md"], ["l1/l2/a.md"]),
    "depth_3": (["l1", "l1/l2", "l1/l2/l3"], ["l1/l2/l3/a.md"], ["l1/l2/l3/a.md"]),
    "dead_end_chain": (["l1", "l1/l2", "l1/l2/l3"], [], []),
    "siblings_with_dead_end": (
        ["x", "x/deep", "y"],
        ["top.md", "x/a.md", "y/b.md"],
        ["top.md", "x/a.md", "y/b.md"],
    ),
    "same_name_different_folders": (["sub"], ["a.md", "sub/a.md"], ["a.md", "sub/a.md"]),
}


@pytest.mark.parametrize(
    "dirs, files, expected",
    FIND_MD_FILES_CASES.values(),
    ids=FIND_MD_FILES_CASES.keys(),
)
def test_find_md_files(dirs, files, expected, tmp_path):
    for name in dirs:
        (tmp_path / name).mkdir()
    for name in files:
        (tmp_path / name).write_text("")

    # Order from os.walk is arbitrary, so compare sorted lists.
    assert sorted(find_md_files(str(tmp_path))) == sorted(expected)


def test_find_md_files_relative_to_given_folder(tmp_path):
    """Paths are relative to the folder passed in, not to anything above it."""
    (tmp_path / "top.md").write_text("")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "c.md").write_text("")

    assert find_md_files(str(tmp_path / "sub")) == ["c.md"]


def test_find_md_files_rejects_missing_folder(tmp_path):
    """A path that doesn't exist raises ValueError."""
    with pytest.raises(ValueError, match="Not a directory"):
        find_md_files(str(tmp_path / "does_not_exist"))
